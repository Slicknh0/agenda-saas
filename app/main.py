from fastapi import FastAPI

from app.routers import appointments, auth, public, services

app = FastAPI(
    title="AgendaSaaS",
    description=(
        "SaaS de agendamento multi-tenant: cada negocio cadastra seus servicos, "
        "clientes finais agendam sem login. Plano free limita servicos ativos."
    ),
    version="0.1.0",
)

app.include_router(auth.router)
app.include_router(services.router)
app.include_router(appointments.router)
app.include_router(public.router)


@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
    return {"status": "ok"}
