from flask_script import Manager, Command
import os
import psycopg2
from pmapi.config import BaseConfig
import shutil
import pexpect
from pmapi.extensions import db
import sys
import tarfile
from datetime import datetime


class SeedTestDb(Command):

    def run(self):
        from pmapi.event_date.model import EventDate

        """
        # drop and recreate db 
        print('Recreating db...')
        # drop db
        drop_db_cmd = 'dropdb -h %s -U %s -p 5432 -f %s ' % (os.environ['SQL_HOST'], os.environ['DATABASE_USER'], os.environ['DATABASE'])      
        child = pexpect.spawn(drop_db_cmd, timeout=20)   
        child.expect('Password: ')
        child.sendline(os.environ['DATABASE_PW'])  
        child.expect(pexpect.EOF)
        # create db
        create_db_cmd = 'createdb -h %s -U %s -p 5432 %s' % (os.environ['SQL_HOST'], os.environ['DATABASE_USER'], os.environ['DATABASE'])      
        child = pexpect.spawn(create_db_cmd, timeout=20)   
        child.expect('Password: ')  
        child.sendline(os.environ['DATABASE_PW'])  
        child.expect(pexpect.EOF)
        print('Recreated db!')
        """

        # restore prod snapshot database
        backup_path = os.path.abspath(
            "snapshot_prod_23_7_22/partymap_23_jul_22.sql")
        print('Hardcoded backup path: ', backup_path)

        # args = ["psql", "-h", "db", "-U", "partymap", "-p", "5432", "partymap", "<", backup_path]
        cmd = '/bin/bash -c "psql -h db -U %s -p %s %s < %s"' % (
            os.environ['DATABASE_USER'], os.environ['SQL_PORT'], os.environ['DATABASE'], backup_path)
        child = pexpect.spawn(cmd, timeout=60)
        print('Restoring db with command: ', cmd)
        try:
            child.expect(pexpect.EOF)
        except:
            pass
        print(child.before)
        print("DB backup restored!")

        print("Restoring uploaded media...")
        # extract and move snapshot of static folder to root
        tar = tarfile.open(os.path.abspath("uploaded_media.tar"))
        # specify which folder to extract to
        tar.extractall(os.path.abspath('static/'))
        tar.close()
        """
        media_src_dir = os.path.abspath("snapshot_prod_23_7_22/static/uploaded_media")
        media_dst_dir = os.path.abspath("static/")
        os.system("cp -rf %s %s" % (media_src_dir, media_dst_dir))  
        """
        print("Media restored!")

        print("Futurising all event_dates...")
        # currently just adding 10 years
        # this could probably be done better
        eds = db.session.query(EventDate).all()
        now = datetime.now()
        for ed in eds:
            timedelta = ed.start - now
            try:
                ed.start = ed.start.replace(year=ed.start.year+2)
                ed.end = ed.end.replace(year=ed.end.year+2)
                ed.start_naive = ed.start_naive.replace(
                    year=ed.start_naive.year+2)
                ed.end_naive = ed.end_naive.replace(year=ed.end_naive.year+2)
            except ValueError as error:
                print('error changing date for: ', ed, " (" + ed.event.name + ", " +
                      str(ed.start_naive) + " => " + str(ed.end_naive) + ") ", error)
        db.session.commit()
        print("EventDates objects are now all in the future! Partytime!")
