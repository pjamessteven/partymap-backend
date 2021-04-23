from pmapi.common import permissions
import pmapi.exceptions as exc
from pmapi.event import controllers as events
from flask_login import current_user


class delete(permissions.Permission):
    """Can delete if staff or event owner"""

    def can(self, **kwargs):
        event = events.get_event_or_404(kwargs.pop("event_id"))

        if (
            event.creator_id != current_user.id
            and not permissions.current_user_role_is_at_least("STAFF")
        ):
            raise exc.InvalidPermissions(
                "You don't have permission to delete this event date."
            )

        return True


class update(permissions.Permission):
    """Can update if staff or event owner"""

    def can(self, **kwargs):
        event = events.get_event_date_or_404(kwargs.pop("event_id"))

        if (
            event.creator_id != current_user.id
            and not permissions.current_user_role_is_at_least("STAFF")
        ):
            raise exc.InvalidPermissions(
                "You don't have permission to update this event date."
            )

        return True


class add(permissions.Permission):
    """Can create if at least HOST"""

    def can(self, **kwargs):
        if not permissions.current_user_role_is_at_least("HOST"):
            raise exc.InvalidPermissions("You don't have permission to create events.")

        return True
