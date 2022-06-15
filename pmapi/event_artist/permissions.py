from pmapi.common import permissions
import pmapi.exceptions as exc
from . import controllers as event_artists
from pmapi.event import controllers as events
from flask_login import current_user


class delete(permissions.Permission):
    """Can delete ifSTAFF"""

    def can(self, **kwargs):

        if not permissions.current_user_role_is_at_least("STAFF"):
            raise exc.InvalidPermissions("You don't have permission.")

        return True


class update(permissions.Permission):
    """Can update if STAFF"""

    def can(self, **kwargs):
        if not permissions.current_user_role_is_at_least("STAFF"):
            raise exc.InvalidPermissions("You don't have permission.")

        return True
