# PartyMap API (PMAPI) — System Design Summary for LLMs

> Target audience: AI coding assistants and new developers onboarding to the codebase.

---

## 1. Project Identity

- **Name:** PartyMap API (PMAPI)
- **Purpose:** Backend for a global festival & event discovery platform (https://www.partymap.com).
- **Human authorship:** This codebase was written by a human developer before the widespread use of generative AI coding assistants.

---

## 2. Tech Stack

| Layer | Technology |
|-------|-----------|
| Language | Python 3.12 |
| Web Framework | Flask 2.3.3 |
| ORM / DB | SQLAlchemy 1.4 + PostgreSQL 15 + PostGIS |
| Migrations | Alembic (Flask-Migrate) |
| API Docs | Flask-Apispec (Swagger/OpenAPI) |
| Auth | Flask-Login + OAuth (Google, Facebook) + API keys |
| Async Tasks | Celery 5.4 + RabbitMQ |
| Caching | Flask-Caching (Redis backend) |
| Geo | GeoAlchemy2, Google Maps API, GeoIP2 |
| Testing | pytest, pytest-flask, testing-postgresql |
| Packaging | uv (replaces pip) |

---

## 3. High-Level Architecture

```
┌─────────────┐     HTTPS      ┌─────────────┐
│   Client    │───────────────▶│ Flask API   │
│  (Quasar)   │◀───────────────│  (PMAPI)    │
└─────────────┘                └──────┬──────┘
                                      │
                    ┌─────────────────┼─────────────────┐
                    │                 │                 │
             ┌──────▼──────┐   ┌──────▼──────┐   ┌─────▼──────┐
             │ PostgreSQL  │   │   RabbitMQ  │   │   Redis    │
             │  + PostGIS  │   │  (Celery)   │   │  (cache)   │
             └─────────────┘   └─────────────┘   └────────────┘
```

---

## 4. Key Domain Models

### Event
- Represents a festival or party (name, description, tags, media).
- Versioned with `sqlalchemy-continuum`.
- Has many `EventDate`s (one event can recur at different dates).

### EventDate
- A specific occurrence of an Event (start, end, timezone, location, artists, tickets).
- Core query surface: geo bounds, distance radius, date ranges, tags, artists.
- `distance` is a `query_expression()` populated dynamically via `with_expression(...)` for location-based queries.

### EventLocation
- Venue / place (name, lat/lng, geo POINT, address components).
- Supports server-side clustering (zoom-level tables `clusters_2` … `clusters_16`).

### User
- Roles: `UNPRIVILIGED_USER`, `ADMIN`, `STAFF`, etc.
- Activities (interested / going / following) tracked via association tables.

### Supporting Models
- `EventArtist`, `EventReview`, `MediaItem`, `EventTag`, `SuggestedEdit`, `Report`, `Activity`, `Notification`

---

## 5. Important Implementation Details

### 5.1 Geo Queries
- PostGIS `Geography` type is used for accurate great-circle distances.
- `ST_Distance`, `ST_DWithin`, `ST_Intersects`, `ST_MakeEnvelope` are used heavily in `pmapi/event_date/controllers.py`.
- The frontend sends `bounds` (`_northEast` / `_southWest`) for map-based filtering.

### 5.2 Query Expression Caching Bug
- `EventDate.distance` is a `query_expression()`.
- SQLAlchemy can return the same identity-mapped instance across queries in the same session.
- **Fix:** `query_event_dates()` uses `.populate_existing()` on the aliased query so `with_expression` values are refreshed on every call.

### 5.3 Celery Tasks
- `pmapi/celery_tasks.py` defines async work:
  - Artist metadata enrichment
  - Media processing (thumbnails, video transcoding)
  - Event embedding generation for semantic search
  - Email / notification dispatch

### 5.4 Database Configuration for Tests
- `Config_Test` reads `TEST_DATABASE_URL` from the environment (set by `docker-compose.test.yml`).
- `testing-postgresql` creates a temporary DB per test and cleans up automatically.

---

## 6. API Route Map

| Blueprint | Prefix | Key Endpoints |
|-----------|--------|---------------|
| `events` | `/api/event` | `GET /`, `POST /`, `GET /<id>`, `PUT /<id>`, `DELETE /<id>` |
| `dates` | `/api/date` | `GET /`, `POST /`, `GET /<id>`, `PUT /<id>`, `DELETE /<id>` |
| `locations` | `/api/location` | `GET /`, `GET /<place_id>`, `GET /points` |
| `artists` | `/api/artist` | `GET /`, `GET /<id>`, `POST /` |
| `users` | `/api/user` | `GET /`, `GET /<id>`, `PUT /<id>` |
| `auth` | `/api/auth` | `POST /login`, `POST /logout`, OAuth flows |
| `search` | `/api/search` | `GET /` |
| `media` | `/api/media` | `POST /`, `DELETE /<id>` |
| `contributions` | `/api/contribution` | `GET /`, `POST /` (reviews) |
| `tags` | `/api/tag` | `GET /` |
| `activity` | `/api/activity` | `GET /` |
| `suggestions` | `/api/suggestions` | `GET /`, `POST /` |
| `metrics` | `/api/metrics` | `GET /` |

---

## 7. Testing Strategy

- **Framework:** pytest + pytest-flask
- **DB Strategy:** testing-postgresql creates a fresh Postgres instance per test; tables are created/dropped automatically.
- **Factories:** `conftest.py` provides `complete_event_factory`, `event_location_factory`, `user_factory`, etc.
- **Run:** `docker compose -f docker-compose.test.yml up --abort-on-container-exit`
- **CI:** GitHub Actions (`test` + `lint` jobs)

---

## 8. Build & Deployment

- **Local dev:** `docker compose -f docker-compose.dev.yml up`
- **Tests:** `docker compose -f docker-compose.test.yml up --abort-on-container-exit`
- **Dependencies:** Managed with `uv` (`uv sync`, `uv add`, `uv run`)
- **Lint:** `ruff check .` + `black --check .`

---

## 9. Common Pitfalls for LLMs

1. **Geo bounds:** `ST_MakeEnvelope` does NOT wrap the antimeridian. The frontend normalizes bounds before sending.
2. **UTC vs naive datetimes:** `EventDate.start` and `EventDate.end` are stored in UTC. Tests must pass UTC-aware datetimes (or the exact stored values) to date filters.
3. **Identity map / `with_expression`:** Never assume `query_expression()` values are fresh across multiple queries in the same session without `populate_existing()`.
4. **Docker DB URL:** Inside containers, `localhost:5439` does not work. Use the `TEST_DATABASE_URL` env var (already configured in `docker-compose.test.yml`).
5. **pytest.approx:** PostGIS distance calculations have tiny floating-point variance; always use `pytest.approx(..., abs=1e-3)` for distance assertions.

---

## 10. Entry Points

- **App factory:** `pmapi/application.py::create_app()`
- **CLI / management:** `manage.py` (Flask-Script style)
- **Celery worker:** `pmapi/celery_worker.py`
- **Config:** `pmapi/config.py` (DevConfig / ProdConfig / TestConfig)
- **Extensions:** `pmapi/extensions.py` (db, cache, lm, cors, admin, apidocs, tracker)
