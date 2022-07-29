from flask_script import Manager, Command
import os
import psycopg2
from pmapi.config import BaseConfig
import shutil
from pmapi.extensions import db

class SeedTestDb(Command):
    def run(self):
        from pmapi.event_date.model import EventDate

        conn = psycopg2.connect(
                host=os.environ['SQL_HOST'],
                database=os.environ['DATABASE'],
                user=os.environ['DATABASE_USER'],
                password=os.environ['DATABASE_PW'])

        # Open a cursor to perform database operations
        cur = conn.cursor()

        # restore prod snapshot database
        backup_path = os.path.abspath("prod_snapshot_july_22/partymap_23_jul_22.sql")
        cur.execute("RESTORE DATABASE partymap FROM DISK=N'{0}'".format(backup_path))

        conn.commit()

        cur.close()
        conn.close()

        # move snapshot of static folder to root
        shutil.move("prod_snapshot_july_22/static", "static")

        print("db restored")
        print("futurising all event_dates...")

        eds = db.session.query(EventDate).all()
        now = datetime.now()
        for ed in eds:
                timedelta = ed.start - now
                ed.start = ed.start + timedelta
                ed.end = ed.end + timedelta
                ed.start_naive = ed.enstart_naived + timedelta
                ed.end_naive = ed.end_naive + timedelta

        db.session.commit()
        print("event_dates are now all in the future")
