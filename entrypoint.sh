#!/bin/sh

# Set uv to use the venv created during build (outside of volume mount)
export UV_PROJECT_ENVIRONMENT=/opt/venv

if [ "$DATABASE" = "postgres" ]
then
    echo "Waiting for postgres..."

    while ! nc -z $SQL_HOST $SQL_PORT; do
      sleep 0.1
    done

    echo "PostgreSQL started"
    
    # Wait a bit more for PostgreSQL to be fully ready
    sleep 2
fi

# Function to run psql with retry
run_psql_with_retry() {
    local cmd="$1"
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if psql -h $SQL_HOST -U $DATABASE_USER -d $DATABASE -c "$cmd" 2>/dev/null; then
            return 0
        fi
        echo "Waiting for database to be ready... (attempt $attempt/$max_attempts)"
        sleep 1
        attempt=$((attempt + 1))
    done
    
    echo "Failed to connect to database after $max_attempts attempts"
    return 1
}

# ensure that postgis extension is enabled
run_psql_with_retry "CREATE EXTENSION IF NOT EXISTS postgis;"
run_psql_with_retry "CREATE EXTENSION IF NOT EXISTS hstore;"
run_psql_with_retry "CREATE EXTENSION IF NOT EXISTS vector;"

# run db migrations
# Only run db init if migrations directory doesn't exist
if [ ! -d "/app/migrations" ] || [ -z "$(ls -A /app/migrations 2>/dev/null)" ]; then
    echo "Initializing migrations directory..."
    uv run python manage.py db init
fi
uv run python manage.py db upgrade

# increase default character limit for flask_usage (flask-track-usage) table
# Only run if the tables exist (they are created by flask-track-usage, not migrations)
run_psql_with_retry "DO \$\$ BEGIN IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'flask_usage') THEN ALTER TABLE flask_usage ALTER COLUMN url TYPE varchar(512); END IF; END \$\$;"
run_psql_with_retry "DO \$\$ BEGIN IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'flask_usage') THEN ALTER TABLE flask_usage ALTER COLUMN blueprint TYPE varchar(64); END IF; END \$\$;"
run_psql_with_retry "DO \$\$ BEGIN IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'flask_usage_useragent_monthly') THEN ALTER TABLE flask_usage_useragent_monthly ALTER COLUMN useragent TYPE varchar(512); END IF; END \$\$;"


if [ "$FLASK_ENV" = "development" ]
then
    echo "Starting dev server..."

    exec uv run python manage.py runserver --host=0.0.0.0
fi


if [ "$FLASK_ENV" = "production" ]
then
    echo "Starting uwsgi..."

    exec uv run uwsgi --ini uwsgi.ini
fi
