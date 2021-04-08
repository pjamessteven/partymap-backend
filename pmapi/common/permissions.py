from functools import partial

from flask_login import current_user

from pmapi.exceptions import InvalidPermissions
from pmapi.utils import ROLES


class Permission(object):
    def __init__(self, func=None, **kwargs):
        self.func = func
        self.kwargs = kwargs
        if func:
            self.add_doc(func)
            # necessary for this decorator to behave well with both decorated
            # functions and class methods
            for n in set(dir(func)) - set(dir(self)):
                setattr(self, n, getattr(func, n))

    def add_doc(self, func):
        if hasattr(func, "__apispec__"):
            docs = func.__apispec__.get("docs")
            if docs:
                try:
                    docs[0].options[0]["description"] = (
                        docs[0].options[0].get("description", "")
                        + "\n##Permissions:\n"
                        + self.__doc__
                    )
                except Exception:
                    pass

    def can(self, **kwargs):
        return True

    def __get__(self, instance, cls, **kwargs):
        return partial(self, instance)

    def __call__(self, *args, **kwargs):
        if self.can(**kwargs):
            return self.func(*args, **kwargs)

    def __enter__(self):
        if self.can(**self.kwargs):
            return self

    def __exit__(self, *args):
        return False


def current_user_role_is_at_least(role):
    """Return true if the requesting user.role is at or above role"""
    return current_user.role >= ROLES.get(role, None)


def user_role_is_at_least(user, role):
    """Return true if the specified user.role is at or above role"""
    return user.role >= ROLES.get(role, None)


class requires_dev_role(Permission):
    """Developer user required"""

    def can(self, **kwargs):
        if current_user_role_is_at_least("DEVELOPER"):
            return True
        raise InvalidPermissions("DEVELOPER or higher role required")


# Permissions decorators / context managers
class requires_admin_role(Permission):
    """Admin user required"""

    def can(self, **kwargs):
        if current_user_role_is_at_least("ADMIN"):
            return True
        raise InvalidPermissions("ADMIN role required")


class requires_staff_role(Permission):
    """Staff+ role required"""

    def can(self, **kwargs):
        if current_user_role_is_at_least("STAFF"):
            return True
        raise InvalidPermissions("STAFF or higher role required")
