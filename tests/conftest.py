import os

# Configura o ambiente ANTES de importar a app: um segredo forte satisfaz a
# validacao de boot e o rate limiting fica desligado para os testes nao
# dependerem de contagem por IP entre casos.
os.environ.setdefault("JWT_SECRET", "test-secret-0123456789-0123456789-abcd")
os.environ.setdefault("RATE_LIMIT_ENABLED", "false")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.db import Base, get_db
from app.main import app


@pytest.fixture()
def client():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def registered_tenant(client):
    resp = client.post(
        "/auth/register",
        json={
            "tenant_name": "Salao Teste",
            "tenant_slug": "salao-teste",
            "email": "dono@salaoteste.com",
            "password": "senha1234",
        },
    )
    assert resp.status_code == 201, resp.text
    token = resp.json()["access_token"]
    return {"token": token, "slug": "salao-teste"}


@pytest.fixture()
def auth_headers(registered_tenant):
    return {"Authorization": f"Bearer {registered_tenant['token']}"}
