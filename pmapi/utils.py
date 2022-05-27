import random
import string

ROLES = {"UNPRIVILIGED_USER": 0, "HOST": 10, "STAFF": 20, "ADMIN": 30}

ACCOUNT_STATUSES = ["active", "disabled", "pending"]

chars = string.ascii_letters + string.digits


def random_string(length=32):
    return "".join(random.SystemRandom().choice(chars) for _ in range(length))
