import random
import string

ROLES = {"USER": 10, "STAFF": 20, "ADMIN": 30}

chars = string.ascii_letters + string.digits

def random_string(length=32):
    return "".join(random.SystemRandom().choice(chars) for _ in range(length))
