How to run the PartyMap Flask backend (PMAPI) on Mac or Linux:


SETUP YOUR LOCAL ENVIRONMENT

Install Python3 

>sudo apt install python3 python3-pip 
(Or for Mac follow these instructions https://docs.python-guide.org/starting/install3/osx/)

1) Set up the database

First you need to install Postgres. 
>sudo apt install postgresql (or for Mac: https://www.postgresql.org/download/macosx/)

Create a database with the command:
>sudo su - postgres -c "createdb partymap"

Then you need to add the postgis extension which PartyMap uses to calculate distances to events on the fly
>sudo su - postgres // login as postgres user
>psql -d partymap // connect to database
>CREATE EXTENSION postgis; // add postgis extension
>\q // exit postgres console
>su 'your username' // switch users back to your main user

You might need do also run this command in the Postgres console..
ALTER TABLE spatial_ref_sys OWNER TO <your-username>;

2) Enter the venv

If you're not familiar with python development, virtual environments (venv) are often used to seperate local dependency packages from global/system python packages. 
This way you can be sure that you have the correct version of all the dependencies installed, and that they won't interfere with other programs on your computer. 
There is already a venv in this project, you can enter into it using the source command:

>source env/bin/activate

3) Install python project dependencies into your virtual environment

>pip3 install -R requirements.txt 

4) Create database tables

>python3 manage.py db upgrade



RUNNING PMAPI OMCE YOU'RE ALL SET UP

1) Enter your venv if you're not already in it
>source venv/bin/activate

2) Set debug environment variable (so PMAPI knows it's running locally)
>export FLASK_DEBUG=1

2) Run celery

PartyMap uses celery for some tasks that can happen asynchronously, at the moment for converting video in the background (uploading video is possible!) 
and refreshing artist profiles with information from last.fm and spotify. If these tasks weren't handed off to a-synchronous worker threads (which is what celery does)
it would make some operations really slow. An example of this would be if someone adds an event where there's a huge lineup and none of the artists are already in the DB, so PMAPI does a lookup on last.fm and spotify for 
every artist. This would take a lot of time and the end-user would be staring at a loading indicator for ages, when these things are really not that important, they can be done 'later' using celery. 

>celery -A pmapi.tasks worker (& to run in background)  

3) Run rabbitmq

Rabbitmq is used by celery for the main application thread to be able to talk to the celery worker threads. 

>sudo rabbitmq-server -detached

4) Run PMAPI

>python3 manage.py runserver


git+http://git.example.com/MyProject#egg=MyProject
git+https://github.com/ashcrow/flask-track-usage@629ad1c#egg=Flask-Track-Usage

Additional Notes: 


-Video converting requires ffmpeg and ffprobe to be installed.

UWSGI command for production:
(Something like..) uwsgi --http-socket :5000 --plugin python37 --module=wsgi:app --virtualenv /home/partymap/partymap-backend/env

Recreate database:
sudo su - postgres -c "dropdb partymap"
sudo su - postgres -c "createdb partymap"
psql -d partymap // connect to database
CREATE EXTENSION postgis; // add postgis extension
python3 manage.py db init



____ 
Steps to get the PMAPI docker container up and running on Mac and Linux:

1) Make sure you have Docker installed on your system!

1) Navigate to the project root
> cd ~/wherever/the/project/is/partymap-backend

2) Pull images
> docker-compose pull

3) Build images
> docker-compose build

4) Run containers
> docker-compose up

6) 
	6A) If you want to your database filled with events, populate your local database with events from production snapshot
		> docker-compose exec web python3 manage.py seed_db

	6B) If you want a fresh testing environment, you will just need to create the default users in the database (admin, anon, partymap-bot):
		> docker-compose exec web python3 manage.py create_users


Handy commands:

Make a new database migration:
docker-compose exec web python3 manage.py db migrate
	
Upgrade to the latest database migration:
docker-compose exec web python3 manage.py db upgrade

Completely destroy database:
docker-compose exec db dropdb -U partymap -f partymap

Create empty database:
docker-compose exec db createdb -U partymap partymap

Seed database with production snapshot:
docker-compose exec web python3 manage.py seed_db


_____
How to backup the production Postgresql DB:
1. Login to prod machine or other environment via ssh
2. Switch to the postgres user
>sudo su - postgres
3. > psql 
4. Dump
How to restore a backup (in docker container)
1. Open a shell for the web service
2. Run: psql -h db -U partymap -p 5432 partymap < snapshot_prod_23_7_22/partymap_23_jul_22.sql
3. Move static folder to root (for media)
_____

