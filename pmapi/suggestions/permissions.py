from pmapi.common import permissions
import pmapi.exceptions as exc
from pmapi.event import controllers as events
from flask_login import current_user


class get(permissions.Permission):
    """Can only get suggestions if admin or higher"""

    def can(self, **kwargs):

        if not permissions.current_user_role_is_at_least("ADMIN"):
            raise exc.InvalidPermissions(
                "You don't have permission to delete this event date."
            )

        return True


class delete(permissions.Permission):
    """Can delete if admin or event owner"""

    def can(self, **kwargs):
        event = events.get_event_or_404(kwargs.get("event_id"))

        if (
            event.creator_id != current_user.id
            and not permissions.current_user_role_is_at_least("ADMIN")
        ):
            raise exc.InvalidPermissions(
                "You don't have permission to delete this event date."
            )

        return True


class update(permissions.Permission):
    """Can update if staff or event owner"""

    def can(self, **kwargs):
        if permissions.current_user_role_is_at_least("ADMIN"):
            return True

        else:
            raise exc.InvalidPermissions(
                "You don't have permission to update this event date."
            )


class add(permissions.Permission):
    """Anyone can create"""

    def can(self, **kwargs):
        # if not permissions.current_user_role_is_at_least("HOST"):
        #    raise exc.InvalidPermissions("You don't have permission to create events.")

        return True
