from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.config import settings

# Limiter global por IP de origem. Armazenamento em memoria: suficiente para
# uma instancia. Atras de proxy, garanta que o IP real chegue (X-Forwarded-For
# tratado pelo proxy/uvicorn --proxy-headers). Em teste, rate_limit_enabled=false.
limiter = Limiter(
    key_func=get_remote_address,
    enabled=settings.rate_limit_enabled,
    default_limits=[],
)
