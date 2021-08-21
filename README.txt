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
celery -A pmapi.tasks worker