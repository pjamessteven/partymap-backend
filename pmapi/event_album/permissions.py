from pmapi.common import permissions
import pmapi.exceptions as exc
from . import controllers as event_albums
from pmapi.event import controllers as events
from flask_login import current_user


class delete_album(permissions.Permission):
    """Can delete if owner or STAFF"""

    def can(self, **kwargs):
        album = event_albums.get_event_album_or_404(kwargs.pop("id"))

        if (
            album.creator_id != current_user.id
            and not permissions.current_user_role_is_at_least("STAFF")
        ):
            raise exc.InvalidPermissions(
                "You don't have permission to delete this event date."
            )

        return True


class update_album(permissions.Permission):
    """Can update if owner or STAFF"""

    def can(self, **kwargs):
        album = event_albums.get_event_album_or_404(kwargs.pop("id"))

        if (
            album.creator_id != current_user.id
            and not permissions.current_user_role_is_at_least("STAFF")
        ):
            raise exc.InvalidPermissions(
                "You don't have permission to update this event date."
            )

        return True


class update_album_item(permissions.Permission):
    """Can update if owner or STAFF"""

    def can(self, **kwargs):
        item = event_albums.get_album_item_or_404(kwargs.pop("id"))

        if (
            item.creator_id != current_user.id
            and not permissions.current_user_role_is_at_least("STAFF")
        ):
            raise exc.InvalidPermissions(
                "You don't have permission to update this event date."
            )

        return True


class delete_album_item(permissions.Permission):
    """Can update if owner or STAFF"""

    def can(self, **kwargs):
        item = event_albums.get_album_item_or_404(kwargs.pop("id"))

        if (
            item.creator_id != current_user.id
            and not permissions.current_user_role_is_at_least("STAFF")
        ):
            raise exc.InvalidPermissions(
                "You don't have permission to update this event date."
            )

        return True
