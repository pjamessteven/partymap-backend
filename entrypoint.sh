#!/bin/sh

if [ "$DATABASE" = "postgres" ]
then
    echo "Waiting for postgres..."

    while ! nc -z $SQL_HOST $SQL_PORT; do
      sleep 0.1
    done

    echo "PostgreSQL started"
fi

# ensure that postgis extension is enabled
psql -h $SQL_HOST -U $DATABASE_USER -d $DATABASE -c "CREATE EXTENSION postgis;"
psql -h $SQL_HOST -U $DATABASE_USER -d $DATABASE -c "CREATE EXTENSION hstore;"

# run db migrations
python manage.py db init
python manage.py db upgrade

# increase default character limit for flask_usage (flask-track-usage) table
psql -h $SQL_HOST -U $DATABASE_USER -d $DATABASE -c "ALTER TABLE flask_usage ALTER COLUMN url TYPE varchar(512);"
psql -h $SQL_HOST -U $DATABASE_USER -d $DATABASE -c "ALTER TABLE flask_usage ALTER COLUMN ip_info TYPE varchar(2048);"
psql -h $SQL_HOST -U $DATABASE_USER -d $DATABASE -c "ALTER TABLE flask_usage ALTER COLUMN blueprint TYPE varchar(64);"


if [ "$FLASK_ENV" = "development" ]
then
    echo "Starting dev server..."

    exec python manage.py runserver --host=0.0.0.0
fi


if [ "$FLASK_ENV" = "production" ]
then
    echo "Starting uwsgi..."

    exec uwsgi --ini uwsgi.ini
fi

