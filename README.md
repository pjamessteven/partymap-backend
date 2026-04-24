# PartyMap Flask backend (PMAPI)

The backend for the global directory of festivals and events (https://www.partymap.com).

Please find the source for the PartyMap Frontend at https://github.com/pjamessteven/partymap-quasar-v2/

---

## License

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

This work is licensed under the [Apache License, Version 2.0](http://www.apache.org/licenses/LICENSE-2.0).

The Apache License 2.0 allows users to use, modify, and distribute this work, even for commercial purposes as long as permission is granted. This license also provides an express grant of patent rights from contributors to users. For more details, see the LICENSE file in the repository.

---

## Contributing

Keen to contribute? Hell yeah!!! Let's build the best event platform on the internet!

You can find us on Discord: https://discord.gg/BD7BwrZA

To start contributing to the code base, [find](https://github.com/pjamessteven/partymap-quasar-v2/issues?q=is:issue+is:closed) an existing issue, or [open](https://github.com/pjamessteven/partymap-quasar-v2/issues/new/choose) a new one. We categorize issues into 2 types:

- Feature requests:
  - If you're opening a new feature request, we'd like you to explain what the proposed feature achieves, and include as much context as possible
  - If you want to pick one up from the existing issues, simply drop a comment below it saying so.

- Anything else (e.g. bug report, performance optimization, typo correction):
  - Start coding right away.

---

## Dependency Management with uv

This project uses [uv](https://docs.astral.sh/uv/) for fast Python dependency management. While the app runs in Docker, you'll use uv locally to manage dependencies.

### Install uv

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Common uv Commands

| Task | Command |
|------|---------|
| Install dependencies (creates/updates lock file) | `uv sync` |
| Add a production package | `uv add <package>` |
| Add a dev package | `uv add --group dev <package>` |
| Update lock file after manual pyproject.toml edits | `uv lock` |
| Run tests | `uv run pytest` |
| Format code | `uv run black .` |
| Lint code | `uv run flake8` |

### Adding a New Dependency

1. Add the package using uv:
   ```bash
   uv add <package-name>
   ```

2. Rebuild the Docker image to include the new dependency:
   ```bash
   docker compose -f docker-compose.dev.yml build --no-cache web
   docker compose -f docker-compose.dev.yml up -d
   ```

---

## Overview

I dockerized PMAPI because it has dependencies like rabbitmq, celery and postgres that can be annoying to manually set up. If you haven't used Docker before, basically it automates the creation of virtual machines images that are set up the same every time according to a script. The file `docker-compose.yml` contains the definitions for each of the creation and configuration of the four services that make up PMAPI. These services all talk to each other over a virtual network. The hostname of each machine or 'service' on the network is simply the name of the service as defined in `docker-compose.yml`.

These containers are:

- `web`: This is the main container which contains and runs the Python Flask application. The base is Debian 12 'Bookworm' with Python 3.12. When docker builds this image, it follows the script in the file named 'Dockerfile'. This script uses apt to install some system packages that are dependencies of the project. It also installs all of the 3rd party Python packages defined in `pyproject.toml` and locked in `uv.lock` using [uv](https://docs.astral.sh/uv/) for fast, reliable dependency management. Environment variables (mostly used by the flask app, see `config.py`) are defined in the file `.env.dev`. You will need to rebuild this image if you add or change any environment variables.

- `db`: This is the Postgresql database configured with the Postgis extension (for geo features like getting distances between two points extremely fast with a SQL query). This image is based on Alpine Linux (a very minimal distro). When first built, the image creates a database with the name and password defined in the environment variables.

- `rabbit`: Rabbitmq is used as a message broker between the main PMAPI Flask thread and additional worker threads (using celery). These celery workers are used so we can hand over heavy or a-synchronous work to another thread while the main Flask thread continues and returns a response. For example, celery is used when we add an event, to handle getting the information for each artist in the lineup if it doesn't already exist in the database. If we didn't hand it off to another worker thread using celery then the user would be staring at a loading spinner for wayyy too long and wonder wtf is going if we hold up the main thread with work that takes a lot of time and could be done async.

- `worker_1`: A celery worker that waits for asynchronous work (like getting artist info and processing media) and then does it 'in the background'. Explained above. This uses the same Debian container created by the 'web' service.

## Testing

Tests run inside Docker against a real PostgreSQL/PostGIS database using `docker-compose.test.yml`.

### Run the full test suite

```bash
docker compose -f docker-compose.test.yml up --abort-on-container-exit
```

This spins up a test database and a test-runner container, then executes `pytest tests/ -v --tb=short`.

### Run a specific test or file during development

```bash
docker compose -f docker-compose.test.yml run --rm test-runner \
  sh -c "uv run pytest tests/test_event_date.py -xvs"
```

### Tips to speed up test execution

1. **Run only changed / targeted tests**  
   During development, scope pytest to the file or test you are working on instead of the full suite:
   ```bash
   uv run pytest tests/test_event.py::test_add_event -xvs
   ```

2. **Use `pytest-timeout`**  
   A 2-minute default timeout is configured. If you are debugging a single test, disable or raise it:
   ```bash
   uv run pytest tests/test_event_date.py -x --timeout=300
   ```

3. **Avoid redundant Docker rebuilds**  
   The test compose file mounts the project root as a volume, so source changes are reflected immediately without rebuilding the image.

4. **Parallel execution (`pytest-xdist`)**  
   The test database is created and dropped per test via `testing-postgresql`, so parallel runs are currently limited by DB contention. For substantial speed-ups, consider switching the test fixtures to use a single shared DB with transaction rollbacks (instead of per-test DB creation) and then run:
   ```bash
   uv run pytest -n auto
   ```

5. **Skip coverage in local dev**  
   If you have coverage plugins enabled locally, omit `--cov` during day-to-day TDD to shave off seconds.

---

## CI / Automated Checks

GitHub Actions runs on every push and pull request to `main`, `master`, and `develop`:

- **`test` job** — starts a PostgreSQL container, installs dependencies via `uv`, and runs `pytest tests/ --tb=short -q`
- **`lint` job** — runs `ruff check .` and `black --check .`

See `.github/workflows/ci.yml` for the full workflow definition.

---

## Architecture Overview

```text
                    ┌──────────────┐
                    │   Client     │
                    │  (Quasar)    │
                    └──────┬───────┘
                           │ HTTPS
                    ┌──────▼───────┐
                    │  Nginx /     │
                    │  Cloudflare  │
                    └──────┬───────┘
                           │
            ┌──────────────┼──────────────┐
            │              │              │
     ┌──────▼──────┐ ┌─────▼─────┐ ┌─────▼──────┐
     │  Flask API  │ │  Celery   │ │  Swagger   │
     │  (PMAPI)    │ │  Workers  │ │  / Docs    │
     └──────┬──────┘ └─────┬─────┘ └────────────┘
            │              │
            │ RabbitMQ     │
            │ (broker)     │
     ┌──────▼──────┐ ┌─────▼─────┐
     │ PostgreSQL  │ │  Redis    │
     │ + PostGIS   │ │  (cache)  │
     └─────────────┘ └───────────┘
```

### Key Components

| Service | Technology | Responsibility |
|---------|-----------|----------------|
| **Web** | Flask 2.3 + SQLAlchemy 1.4 | REST API, request handling, business logic |
| **DB** | PostgreSQL 15 + PostGIS | Persistent storage, geospatial queries (`ST_Distance`, `ST_Intersects`) |
| **Message Broker** | RabbitMQ | Celery task queue (artist lookups, media processing, email) |
| **Workers** | Celery 5 | Background/async jobs (scraping, image processing, embedding generation) |
| **Cache** | Redis (via Flask-Caching) | Rate limiting, response caching |
| **Auth** | Flask-Login + OAuth (Google, FB) | Session and token-based authentication |
| **Docs** | Flask-Apispec | Auto-generated Swagger/OpenAPI specs at `/swagger-ui/` |

### Domain Modules & Routes

| Blueprint | URL Prefix | What it does |
|-----------|-----------|--------------|
| `events` | `/api/event` | CRUD for events, versioning, full-text search |
| `dates` | `/api/date` | Event date instances, filtering by geo bounds / distance / time |
| `locations` | `/api/location` | Venues, geo clustering, reverse geocoding |
| `artists` | `/api/artist` | Lineup artists, external metadata (Spotify, etc.) |
| `users` | `/api/user` | Profiles, roles, activity feeds |
| `auth` | `/api/auth` | Login, logout, OAuth callbacks, API key auth |
| `search` | `/api/search` | Global search, vector embeddings |
| `media` | `/api/media` | Image/video upload and processing |
| `contributions` | `/api/contribution` | Reviews, ratings, reports |

> **Note:** This codebase was originally authored by a human developer before the widespread adoption of generative AI coding assistants. Many architectural decisions, schema designs, and business-logic patterns reflect organic, iterative development.

---

## API documentation

See /swagger-ui/ and /swagger/

## Initial install (Docker)

1. Make sure you have Docker and Docker Compose installed on your system!

2. Navigate to the project root

3. Copy .env.dev.example to .env.dev and fill out requisite API keys

4. Pull images

   > docker compose pull

5. Build images

   > docker compose -f docker-compose.dev.yml build --no-cache

6. Run containers

   > docker compose -f docker-compose.dev.yml up

7. - If you want your database prepopulated with events from a partymap.com snapshot:

     > docker compose exec web uv run python manage.py seed_db

   - If you want a fresh testing environment, create the default users:

     > docker compose exec web uv run python manage.py create_users

8. That should be it! Access the API at http://localhost:5000

## Subsequent runs (Docker):

> docker compose up

## Handy commands:

Completely destroy database:

> docker compose exec db dropdb -U partymap -f partymap

Create empty database:

> docker compose exec db createdb -U partymap partymap

Adjust SQLAlchemy tables (do this after recreating the database):

> docker compose exec web ./alter_sqlalchemy_tables.sh

Seed database with production snapshot:

> docker compose exec web uv run python manage.py seed_test_db

Access bash within the main 'web' container:

> docker compose exec -it web /bin/bash

Send any command to a container:

> docker compose exec [container name] [command]

Generate Typescript interfaces from marshmallow schemas (prints to ./autogen_types.ts):

> docker compose exec web uv run python manage.py generate_types

Expose local Docker network to local network (useful for testing on mobile):

> docker compose run --service-ports web

---

## Data migrations

Backfill embeddings:

> docker compose exec web uv run python manage.py backfill_event_embeddings --force

---

## Alembic Postgres Database Management commands:

Make a new database migration:

> docker compose exec web uv run python manage.py db migrate

List all database migrations/revisions:

> docker compose exec web uv run python manage.py db history

Upgrade to the latest database migration:

> docker compose exec web uv run python manage.py db upgrade

Downgrade to a specific migration:

> docker compose exec web uv run python manage.py db downgrade [REVISION_ID]

## Prod notes:

---

Purge celery tasks:

-A pmapi.celery_worker.celery worker purge

# Make requests with the API key

curl -H "X-API-Key: your-api-key-here" \
 -H "Content-Type: application/json" \
 -X POST \
 -d '{"name": "Test Event", "description": "Test", "location": {"description": "NYC"}, "date_time": {"start": "2025-12-25T20:00:00"}}' \
 http://api.partymap.com/api/event/

# Or using query parameter

curl "http://api.partymap.com/api/event/?api_key=your-api-key-here"
