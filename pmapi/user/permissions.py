from pmapi.common import permissions
import pmapi.exceptions as exc
from . import controllers as users
from flask_login import current_user


class get_users(permissions.Permission):
    """Can only get users by role if STAFF"""

    def can(self, **kwargs):
        if not permissions.current_user_role_is_at_least("STAFF"):
            if kwargs.get("role", None) is not None:
                raise exc.InvalidPermissions(
                    "You don't have permission to get users by role."
                )
            if kwargs.get("status", None) is not None:
                raise exc.InvalidPermissions(
                    "You don't have permission to get users by status."
                )
        return True


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


class get_user_full_profile(permissions.Permission):
    """Can get private info if STAFF"""

    def can(self, **kwargs):

        if not permissions.current_user_role_is_at_least("STAFF"):
            raise exc.InvalidPermissions(
                "You don't have permission to update this event date."
            )

        return True
