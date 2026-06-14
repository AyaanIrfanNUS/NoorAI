"""
Shared rate limiter instance.

Defined here (not in main.py) so route modules can import it without
creating a circular import with the main app module.

default_limits applies to every route that doesn't have its own
@limiter.limit(...) decorator. The auth endpoints will override this
with their own stricter limits.
"""
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["60/minute"],
)