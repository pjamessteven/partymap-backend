from pmapi.common import permissions
import pmapi.exceptions as exc
from . import controllers as media_items
from pmapi.event import controllers as events
from flask_login import current_user


class view_metrics(permissions.Permission):
    """Can view if STAFF"""

    def can(self, **kwargs):
        if not permissions.current_user_role_is_at_least("STAFF"):

            raise exc.InvalidPermissions(
                "You don't have permission to view metrics."
            )

        return True