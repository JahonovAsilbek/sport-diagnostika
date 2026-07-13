"""Login brute-force protection (BCKND-69).

Failed logins are counted per (username, IP) in the cache with a fixed window from the first
failure; once the count crosses `LOGIN_LOCKOUT_THRESHOLD` the pair is locked for
`LOGIN_LOCKOUT_COOLDOWN`. Locking is silent — the view returns the same generic error whether or
not the username exists, so lockout never leaks account existence. A cache outage fails OPEN for
the lockout (the DRF `login` rate throttle still caps volume) rather than locking everyone out.
"""

from django.conf import settings
from django.core.cache import cache


def _keys(username, ip):
    ident = f"{(username or '').strip().lower()}|{ip or '-'}"
    return f"login:fail:{ident}", f"login:lock:{ident}"


def is_locked(username, ip):
    _, lock_key = _keys(username, ip)
    try:
        return cache.get(lock_key) is not None
    except Exception:
        return False  # cache down → don't hard-block logins


def register_failure(username, ip):
    """Count a failed attempt and lock the (username, IP) pair once it crosses the threshold.
    Returns True if the pair is now locked."""
    fail_key, lock_key = _keys(username, ip)
    try:
        # add() seeds the counter with the window TTL only on the first failure (so the window
        # runs from that first failure); later failures bump it via incr().
        if cache.add(fail_key, 1, settings.LOGIN_LOCKOUT_WINDOW):
            count = 1
        else:
            count = cache.incr(fail_key)
        if count >= settings.LOGIN_LOCKOUT_THRESHOLD:
            cache.set(lock_key, 1, settings.LOGIN_LOCKOUT_COOLDOWN)
            cache.delete(fail_key)
            return True
    except Exception:
        return False
    return False


def clear_failures(username, ip):
    """Wipe the counter + lock on a successful login."""
    fail_key, lock_key = _keys(username, ip)
    try:
        cache.delete_many([fail_key, lock_key])
    except Exception:
        pass
