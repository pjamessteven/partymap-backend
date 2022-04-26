Celery requires rabbitmq

Video converter requires ffmpeg and ffprobe


Recreate database:
sudo su - postgres -c "dropdb partymap"
sudo su - postgres -c "createdb partymap"

Connect to database:
sudo su - postgres // login as root
psql -d partymap // connect to database
CREATE EXTENSION postgis; // add postgis extension

Might need this..
ALTER TABLE spatial_ref_sys OWNER TO pete;

For runtime:

Run rabbitmq server: 

sudo rabbitmq-server -detached

Run celery worker (in venv):
celery -A pmapi.tasks worker (& to run in background)  

UWSGI command:
(Something like..) uwsgi --http-socket :5000 --plugin python37 --module=wsgi:app --virtualenv /home/partymap/partymap-backend/env

FLASK USAGE TABLE NEEDS FIXING ON DEPLOY
	- URL field length and various other fields

export FLASK_DEBUG=1 for dev


