How to run the PartyMap Flask backend (PMAPI) on Mac or Linux:


Overview:
_____________________________________________________________________________

I dockerized PMAPI because it has dependencies like rabbitmq, celery and postgres that can take a while to set up. 
Docker makes it possible to automate the creation of virtual machines (services) that are set up the same every time according to a script. 
The file docker-compose.yml contains the definitions for each of the creation and configuration of the four services that make up PMAPI. 
These services all talk to each other over a virtual network. The hostname of each machine or 'service' on the network is simply the name of the service as defined in docker-copmose.yml.

These containers are:

'web': 		This is the main container which contains and runs the Python Flask application. The base is Debian 11 'Bullseye'.
		When docker builds this image, it follows the script in the file named 'Dockerfile'.
		This script uses apt to install some system packages that are dependencies of the project. 
		It also installs all of the 3rd party Python packages defined in requirements.txt.
		Environment variables (mostly used by the flask app, see config.py) are defined in the file .env.dev
		You will need to rebuild this image if you add or change any environment variables. 

'db': 		This is the Postgresql database configured with the Postgis extension (for geo features like getting distances between two points extremely fast with a SQL query). 
		This image is based on Alpine Linux (a very minimal distro). 
		When first built, the image creates a database with the name and password defined in the environment variables. 

'rabbit': 	Rabbitmq is used as a message broker between the main PMAPI Flask thread and additional worker threads (using celery). These celery workers 
		are used so we can hand over heavy or a-synchronous work to another thread while the main Flask thread continues and returns a response. 
		For example, celery is used when we add an event, to handle getting the information for each artist in the lineup if it doesn't already exist
		in the database. If we didn't hand it off to another worker thread using celery then the user would be staring at a loading spinner for wayyy
		too long and wonder wtf is going if we hold up the main thread with work that takes a lot of time and could be done async.

'worker_1':	A celery worker that waits for asynchronous work and then does it 'in the background'. Explained above.  This uses the same Debian container created by the 'web' service. 


Initial install: 
_____________________________________________________________________________

1) Make sure you have Docker and Docker Compose installed on your system!

2) Navigate to the project root
> cd ~/wherever/the/project/is/partymap-backend

3) Pull images
> docker compose pull

4) Build images
> docker compose build (--no-cache option can be useful sometimes)

5) Run containers
> docker compose up

6) 	A) If you want to your database prepopulated with events from a partymap.com snapshot
		> docker compose exec web python3 manage.py seed_db

	B) If you want a fresh testing environment, you will just need to create the default users in the database (admin, anon, partymap-bot):
		> docker compose exec web python3 manage.py create_users

7) That should be it! You should now be able to access the api from your local environment at localhost:5000



Subsequent runs: 
_____________________________________________________________________________

> docker compose up



Handy commands:
_____________________________________________________________________________

Completely destroy database:
> docker compose exec db dropdb -U partymap -f partymap

Create empty database:
> docker compose exec db createdb -U partymap partymap

Adjust SQLAlchemy tables (do this after recreating the database)
> docker compose exec web ./alter_sqlalchemy_tables.sh

Seed database with production snapshot:
> docker compose exec web python3 manage.py seed_test_db

Access bash within the main 'web' container:
> docker compose exec -it web /bin/bash

Send any command to a container:
> docker compose exec [container name] [command]

Generate Typescript interfaces from marshmallow schemas (prints to ./autogen_types.ts)
> docker compose exec web python3 manage.py generate_types

Expose local Docker network to local network (useful for testing on mobile)
> docker compose run --service-ports web

_____________________________________________________________________________

Alembic Postgres Database Management commands:

Make a new database migration:
> docker compose exec web python3 manage.py db migrate

List all database migrations/revisions:
> docker compose exec web python3 manage.py db history
	
Upgrade to the latest database migration:
> docker compose exec web python3 manage.py db upgrade

Downgrade to the latest database migration:
> docker compose exec web python3 manage.py db downgrade [REVISION_ID]


Tips related to the production environment:
_____________________________________________________________________________

How to backup the production Postgresql DB:
1) Login to prod machine or other environment via ssh
2) Switch to the postgres user
> sudo su - postgres
3)
 > psql 
4)> Dump

How to restore a backup (in docker container)
1) Open a shell for the web service
2) Run: psql -h db -U partymap -p 5432 partymap < snapshot_prod_23_7_22/partymap_23_jul_22.sql
3) Move static folder to root (for media)


UWSGI command for production:
(Something like..) uwsgi --http-socket :5000 --plugin python37 --module=wsgi:app --virtualenv /home/partymap/partymap-backend/env

_______________________________________________________________________________


Additional Notes: 

-Video converting requires ffmpeg and ffprobe to be installed.

