from pmapi.common import permissions
import pmapi.exceptions as exc
from . import controllers as event_dates
from pmapi.event_review import controllers as reviews
from flask_login import current_user


class delete(permissions.Permission):
    """Can delete if owner or STAFF"""

    def can(self, **kwargs):
        review = reviews.get_review_or_404(kwargs.get("review_id"))

        if (
            review.creator_id != current_user.id
            and not permissions.current_user_role_is_at_least("STAFF")
        ):
            raise exc.InvalidPermissions(
                "You don't have permission to delete this event date."
            )

        return True


class update(permissions.Permission):
    """Can update if owner"""

    def can(self, **kwargs):
        review = reviews.get_review_or_404(kwargs.get("review_id"))

        if (
            review.creator_id != current_user.id
        ):
            raise exc.InvalidPermissions(
                "You don't have permission to delete this event date."
            )

        return True


