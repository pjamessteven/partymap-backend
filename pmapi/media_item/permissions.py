from pmapi.common import permissions
import pmapi.exceptions as exc
from . import controllers as media_items
from pmapi.event import controllers as events
from flask_login import current_user


class update_media_item(permissions.Permission):
    """Can update if event owner, media item owner or STAFF"""

    def can(self, **kwargs):
        item = media_items.get_media_item_or_404(kwargs.pop("id"))
        event = events.get_event_or_404(item.event_id)
        if not permissions.current_user_role_is_at_least("STAFF"):
            if (
                item.creator_id != current_user.id
                and event.creator_id != current_user.id
            ):
                raise exc.InvalidPermissions(
                    "You don't have permission to update this event date."
                )
            return True

        return True


class delete_media_item(permissions.Permission):
    """Can update if event owner, media item owner or STAFF"""

    def can(self, **kwargs):
        item = media_items.get_media_item_or_404(kwargs.pop("id"))
        event = events.get_event_or_404(item.event_id)
        if not permissions.current_user_role_is_at_least("STAFF"):
            if (
                item.creator_id != current_user.id
                and event.creator_id != current_user.id
            ):
                raise exc.InvalidPermissions(
                    "You don't have permission to update this event date."
                )
            return True

        return True
