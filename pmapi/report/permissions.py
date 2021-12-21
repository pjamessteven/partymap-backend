from pmapi.common import permissions
import pmapi.exceptions as exc


class delete_report(permissions.Permission):
    """Can delete if STAFF"""

    def can(self, **kwargs):

        if not permissions.current_user_role_is_at_least("STAFF"):
            raise exc.InvalidPermissions(
                "You don't have permission to update this event date."
            )

        return True


class update_report(permissions.Permission):
    """Can delete if STAFF"""

    def can(self, **kwargs):

        if not permissions.current_user_role_is_at_least("STAFF"):
            raise exc.InvalidPermissions(
                "You don't have permission to update this event date."
            )

        return True


class get_reports(permissions.Permission):
    """Can get if STAFF"""

    def can(self, **kwargs):

        if not permissions.current_user_role_is_at_least("STAFF"):
            raise exc.InvalidPermissions("You don't have permission to get reports.")

        return True
