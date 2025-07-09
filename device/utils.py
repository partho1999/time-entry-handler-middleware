import random
import string
from .constants import WEB_SOCKET, WEB_SOCKET_API_PATH

# RandomUtil equivalents

def get_rand_num(n):
    if n <= 0:
        return 0
    elif n == 1:
        return random.randint(0, 9)
    elif n == 10:
        return 1000000000 + get_rand_num(9)
    elif n > 10:
        raise ValueError("invalid parameter n (n must <= 10)")
    lower = 10 ** (n - 1)
    upper = 10 ** n - 1
    return random.randint(lower, upper)

def get_rand_num4():
    return get_rand_num(4)

def get_rand_num6():
    return get_rand_num(6)

def get_rand_num8():
    return get_rand_num(8)

def get_rand_lower_letter(n):
    return ''.join(random.choices(string.ascii_lowercase, k=n))

def get_rand_upper_letter(n):
    return ''.join(random.choices(string.ascii_uppercase, k=n))

def get_rand_letter(n):
    return ''.join(random.choices(string.ascii_letters, k=n))

def get_rand_string(n):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=n))

# SkipAuthUtil equivalent

def is_skip_auth(request):
    upgrade = request.headers.get('upgrade', '')
    uri = request.path
    return upgrade.lower() == WEB_SOCKET and uri == WEB_SOCKET_API_PATH 