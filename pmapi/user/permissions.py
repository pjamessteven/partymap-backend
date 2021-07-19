from pmapi.common import permissions
import pmapi.exceptions as exc
from . import controllers as users
from flask_login import current_user


class update_user(permissions.Permission):
    """Can update if current_user or STAFF"""

    def can(self, **kwargs):
        user = users.get_user_or_404(kwargs.pop("user_id"))
        if not permissions.current_user_role_is_at_least("STAFF"):
            if user.id != current_user.id:
                raise exc.InvalidPermissions(
                    "You don't have permission to delete this user."
                )
            return True

        return True


class delete_user(permissions.Permission):
    """Can delete if current_user or STAFF"""

    def can(self, **kwargs):
        user = users.get_user_or_404(kwargs.pop("user_id"))
        if not permissions.current_user_role_is_at_least("STAFF"):
            if user.id != current_user.id:
                raise exc.InvalidPermissions(
                    "You don't have permission to delete this user."
                )
            return True

        return True
