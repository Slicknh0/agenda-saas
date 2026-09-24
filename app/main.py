from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded

from app.core.config import settings
from app.core.ratelimit import limiter
from app.routers import appointments, auth, public, services

# Docs interativas (Swagger/Redoc/OpenAPI) so em desenvolvimento; em producao
# ficam fechadas para nao expor a superficie da API.
_docs_kwargs = (
    {}
    if settings.debug
    else {"docs_url": None, "redoc_url": None, "openapi_url": None}
)

app = FastAPI(
    title="AgendaSaaS",
    description=(
        "SaaS de agendamento multi-tenant: cada negocio cadastra seus servicos, "
        "clientes finais agendam sem login. Plano free limita servicos ativos."
    ),
    version="0.1.0",
    **_docs_kwargs,
)

# Rate limiting (brute-force de login e spam de agendamento publico).
app.state.limiter = limiter


@app.exception_handler(RateLimitExceeded)
def _rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    return JSONResponse(
        status_code=429,
        content={"detail": "Muitas requisicoes. Tente novamente em instantes."},
    )


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "no-referrer")
    response.headers.setdefault("Cache-Control", "no-store")
    # HSTS so faz sentido sob HTTPS (producao atras de proxy TLS).
    if not settings.debug:
        response.headers.setdefault(
            "Strict-Transport-Security", "max-age=63072000; includeSubDomains"
        )
    return response


app.include_router(auth.router)
app.include_router(services.router)
app.include_router(appointments.router)
app.include_router(public.router)


@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
    return {"status": "ok"}
