def test_register_creates_tenant_and_returns_token(client):
    resp = client.post(
        "/auth/register",
        json={
            "tenant_name": "Clinica X",
            "tenant_slug": "clinica-x",
            "email": "dona@clinicax.com",
            "password": "senha1234",
        },
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["access_token"]
    assert body["token_type"] == "bearer"


def test_register_rejects_duplicate_slug(client):
    payload = {
        "tenant_name": "Clinica X",
        "tenant_slug": "clinica-x",
        "email": "a@a.com",
        "password": "senha1234",
    }
    client.post("/auth/register", json=payload)

    payload["email"] = "b@b.com"
    resp = client.post("/auth/register", json=payload)
    assert resp.status_code == 409


def test_login_with_correct_credentials(client, registered_tenant):
    resp = client.post(
        "/auth/login",
        json={"email": "dono@salaoteste.com", "password": "senha1234"},
    )
    assert resp.status_code == 200
    assert resp.json()["access_token"]


def test_login_with_wrong_password_fails(client, registered_tenant):
    resp = client.post(
        "/auth/login",
        json={"email": "dono@salaoteste.com", "password": "senha-errada"},
    )
    assert resp.status_code == 401
