from pmapi.event_artist.model import Artist
from sqlalchemy.orm import Session 
from sqlalchemy import event
from pmapi.tasks import refresh_artist_info

# The artist info refresh had to be implented with a listener
# Reason: When I create the artist then commit (so the celery worker can find the artist), 
# then trigger the celery task to refresh info, any code after that point breaks (such as adding subsequent artists) 
# because all objects in the session get detatched once you commit

# Track all modified or new objects in a single set
@event.listens_for(Session, "before_flush")
def track_objects(session, flush_context, instances):
    if not hasattr(session, '_pending_objects'):
        session._pending_objects = set()
    session._pending_objects.update(session.new)
    session._pending_objects.update(session.dirty)

    # exclude objects if flagged to not process
    session._pending_objects = {obj for obj in session._pending_objects if not should_exclude(obj)}


def should_exclude(obj):
    # Exclude objects where `obj.should_process` is set to False
    if hasattr(obj, 'after_commit') and not obj.after_commit:
        return True
    return False

@event.listens_for(Session, "after_commit")
def process_objects_after_commit(session):
    if hasattr(session, '_pending_objects'):
        for instance in session._pending_objects:
            # refresh artist info in background after create or update
            if isinstance(instance, Artist):
                artist_id = instance.id
                refresh_artist_info.delay(artist_id)
                print(f"Artist instance committed or updated: {instance}")
        session._pending_objects.clear()
