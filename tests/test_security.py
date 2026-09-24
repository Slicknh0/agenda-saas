"""Regressao de seguranca: cada teste trava uma correcao de vulnerabilidade."""

from datetime import datetime, timedelta, timezone

import jwt
import pytest

from app.core.config import Settings, settings
from app.core.ratelimit import limiter


def _headers(token):
    return {"Authorization": f"Bearer {token}"}


# ---- JWT ----------------------------------------------------------------

def test_token_signed_with_wrong_secret_is_rejected(client, registered_tenant):
    forged = jwt.encode(
        {"sub": "1", "tenant_id": 1}, "attacker-secret", algorithm=settings.jwt_algorithm
    )
    resp = client.get("/appointments", headers=_headers(forged))
    assert resp.status_code == 401


def test_token_with_non_numeric_sub_returns_401_not_500(client, registered_tenant):
    bad = jwt.encode(
        {"sub": "abc", "tenant_id": 1, "exp": datetime.now(timezone.utc) + timedelta(hours=1)},
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )
    resp = client.get("/appointments", headers=_headers(bad))
    assert resp.status_code == 401


def test_expired_token_is_rejected(client, registered_tenant):
    expired = jwt.encode(
        {"sub": "1", "exp": datetime.now(timezone.utc) - timedelta(hours=1)},
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )
    resp = client.get("/appointments", headers=_headers(expired))
    assert resp.status_code == 401


# ---- Isolamento multi-tenant (BOLA) ------------------------------------

def test_tenant_cannot_touch_other_tenants_appointment(client, registered_tenant):
    # tenant 1 cria servico e recebe um agendamento publico
    t1 = registered_tenant["token"]
    client.post(
        "/services",
        json={"name": "Corte", "duration_minutes": 30, "price_cents": 5000},
        headers=_headers(t1),
    )
    svc_id = client.get("/services", headers=_headers(t1)).json()[0]["id"]
    booked = client.post(
        f"/public/{registered_tenant['slug']}/book",
        json={
            "service_id": svc_id,
            "client_name": "Cliente",
            "client_contact": "11999998888",
            "starts_at": "2027-05-01T10:00:00",
        },
    )
    assert booked.status_code == 201
    appt_id = booked.json()["id"]

    # tenant 2 (outro negocio)
    reg2 = client.post(
        "/auth/register",
        json={
            "tenant_name": "Outro",
            "tenant_slug": "outro-negocio",
            "email": "dono@outro.com",
            "password": "senha1234",
        },
    )
    t2 = reg2.json()["access_token"]

    # nao ve o agendamento alheio
    assert client.get("/appointments", headers=_headers(t2)).json() == []
    # nao consegue cancelar o agendamento alheio
    resp = client.patch(f"/appointments/{appt_id}/cancel", headers=_headers(t2))
    assert resp.status_code == 404


# ---- Validacao de entrada ----------------------------------------------

def test_booking_in_the_past_is_rejected(client, registered_tenant):
    t1 = registered_tenant["token"]
    client.post(
        "/services",
        json={"name": "Corte", "duration_minutes": 30, "price_cents": 5000},
        headers=_headers(t1),
    )
    svc_id = client.get("/services", headers=_headers(t1)).json()[0]["id"]
    resp = client.post(
        f"/public/{registered_tenant['slug']}/book",
        json={
            "service_id": svc_id,
            "client_name": "Cliente",
            "client_contact": "11999998888",
            "starts_at": "2020-01-01T10:00:00",
        },
    )
    assert resp.status_code == 422


# ---- Cabecalhos de seguranca -------------------------------------------

def test_security_headers_present(client):
    resp = client.get("/health")
    assert resp.headers["X-Content-Type-Options"] == "nosniff"
    assert resp.headers["X-Frame-Options"] == "DENY"


# ---- Rate limiting ------------------------------------------------------

def test_login_is_rate_limited(client):
    limiter.enabled = True
    try:
        codes = [
            client.post(
                "/auth/login", json={"email": "x@x.com", "password": "wrongpass"}
            ).status_code
            for _ in range(12)
        ]
    finally:
        limiter.enabled = False
        limiter.reset()
    assert 429 in codes


# ---- Config: segredo fraco barra o boot em producao ---------------------

def test_insecure_secret_blocks_production_boot():
    with pytest.raises(RuntimeError):
        Settings(debug=False, jwt_secret="dev-secret-change-in-production")


def test_short_secret_blocks_production_boot():
    with pytest.raises(RuntimeError):
        Settings(debug=False, jwt_secret="short")


# ---- API4: paginacao limitada ------------------------------------------

def test_list_pagination_is_bounded(client, registered_tenant):
    t1 = registered_tenant["token"]
    resp = client.get("/services?limit=9999", headers=_headers(t1))
    assert resp.status_code == 422  # limit > 200 barrado


def test_list_pagination_limit_applies(client, registered_tenant):
    t1 = registered_tenant["token"]
    # 3 servicos = limite do plano free; suficiente para provar limit=1
    for i in range(3):
        client.post(
            "/services",
            json={"name": f"Servico {i}", "duration_minutes": 30, "price_cents": 1000},
            headers=_headers(t1),
        )
    resp = client.get("/services?limit=1", headers=_headers(t1))
    assert resp.status_code == 200
    assert len(resp.json()) == 1


# ---- API2: senha longa nao derruba o servidor --------------------------

def test_overlong_password_login_returns_401_not_500(client, registered_tenant):
    resp = client.post(
        "/auth/login",
        json={"email": "dono@salaoteste.com", "password": "A" * 500},
    )
    assert resp.status_code == 401
