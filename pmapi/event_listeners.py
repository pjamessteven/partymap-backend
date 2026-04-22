from pmapi.event.model import Event
from pmapi.event_artist.model import Artist
from pmapi.event_date.model import EventDate
from sqlalchemy.orm import Session 
from sqlalchemy import event
from flask.helpers import get_debug_flag
DEV_ENVIRON = get_debug_flag()

# The artist info refresh had to be implented with a listener
# Reason: When I create the artist then commit (so the celery worker can find the artist), 
# then trigger the celery task to refresh info, any code after that point breaks (such as adding subsequent artists) 
# because all objects in the session get detatched once you commit
#
# You must set the after_commit attribute on the object if you want it to be processed!

# Track all modified or new objects in a single set
@event.listens_for(Session, "before_flush")
def track_objects(session, flush_context, instances):
    if not hasattr(session, '_pending_objects'):
        session._pending_objects = set()
    session._pending_objects.update(session.new)
    session._pending_objects.update(session.dirty)
    session._pending_objects.update(
        obj
        for obj in session.identity_map.values()
        if getattr(obj, "refresh_embedding_after_commit", False)
    )
    # exclude objects if flagged to not process
    session._pending_objects = {obj for obj in session._pending_objects if not should_exclude(obj)}


def should_exclude(obj):
    # Exclude objects where `obj.after_commit` is set to False
    if (hasattr(obj, 'after_commit') and obj.after_commit == True):
        return False
    if getattr(obj, "refresh_embedding_after_commit", False):
        return False
    return True

@event.listens_for(Session, "after_commit")
def process_objects_after_commit(session):
    if hasattr(session, '_pending_objects'):
        print('PENDING', session._pending_objects)

        for instance in session._pending_objects:

            # refresh artist info in background after create or update
            if isinstance(instance, Artist):
                print('after_commit: refreshing artist')
                artist_id = instance.id
                from pmapi.celery_tasks import refresh_artist_info
                refresh_artist_info.delay(artist_id)
                print(f"Artist instance committed or updated: {instance}")

            # refresh event description in background after create or update
            if isinstance(instance, Event):
                if getattr(instance, "refresh_embedding_after_commit", False):
                    event_id = instance.id
                    from pmapi.celery_tasks import update_event_embedding
                    update_event_embedding.delay(event_id)
                    instance.refresh_embedding_after_commit = False

                # dont burn tokens in DEV
                if getattr(instance, 'after_commit', False) and (not DEV_ENVIRON or True):
                    event_id = instance.id
                    from pmapi.celery_tasks import update_event_translation
                    update_event_translation.delay(event_id)
                    instance.after_commit = False
                    print(f"Event instance committed or updated: {instance}")

            # refresh event date description in background after create or update
            if isinstance(instance, EventDate):
                # dont burn tokens in DEV
                if getattr(instance, 'after_commit', False) and not DEV_ENVIRON:
                    event_date_id = instance.id
                    from pmapi.celery_tasks import update_event_date_translation
                    update_event_date_translation.delay(event_date_id)
                    instance.after_commit = False
                    print(f"EventDate instance committed or updated: {instance}")

        session._pending_objects.clear()
