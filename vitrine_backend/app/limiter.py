import os
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address, default_limits=[])
if os.getenv("RATE_LIMIT_ENABLED", "1") == "0":
    limiter.enabled = False
