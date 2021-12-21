from pmapi.common import permissions
import pmapi.exceptions as exc
from . import controllers as event_dates
from pmapi.event import controllers as events
from flask_login import current_user


class delete(permissions.Permission):
    """Can delete if host or STAFF"""

    def can(self, **kwargs):
        ed = event_dates.get_event_date_or_404(kwargs.pop("id"))

        if (
            ed.event.host_id != current_user.id
            and not permissions.current_user_role_is_at_least("STAFF")
        ):
            raise exc.InvalidPermissions(
                "You don't have permission to delete this event date."
            )

        return True


class update(permissions.Permission):
    """Can update if host or STAFF"""

    def can(self, **kwargs):
        ed = event_dates.get_event_date_or_404(kwargs.pop("id"))
        if (
            ed.event.host_id != current_user.id
            and not permissions.current_user_role_is_at_least("STAFF")
        ):
            raise exc.InvalidPermissions(
                "You don't have permission to update this event date."
            )

        return True


class add(permissions.Permission):
    """Can add event date to event if host or STAFF"""

    def can(self, **kwargs):

        event = events.get_event(kwargs.pop("event_id"))

        if (
            event.host_id != current_user.id
            and not permissions.current_user_role_is_at_least("STAFF")
        ):
            raise exc.InvalidPermissions(
                "You don't have permission to create a new date for this event."
            )

        return True
