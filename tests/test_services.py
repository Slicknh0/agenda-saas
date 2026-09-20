def test_create_and_list_service(client, auth_headers):
    resp = client.post(
        "/services",
        headers=auth_headers,
        json={"name": "Corte de cabelo", "duration_minutes": 30, "price_cents": 5000},
    )
    assert resp.status_code == 201
    service = resp.json()
    assert service["name"] == "Corte de cabelo"
    assert service["active"] is True

    resp = client.get("/services", headers=auth_headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_create_service_requires_auth(client):
    resp = client.post(
        "/services",
        json={"name": "Corte de cabelo", "duration_minutes": 30, "price_cents": 5000},
    )
    assert resp.status_code == 401


def test_update_service(client, auth_headers):
    created = client.post(
        "/services",
        headers=auth_headers,
        json={"name": "Corte", "duration_minutes": 30, "price_cents": 5000},
    ).json()

    resp = client.patch(
        f"/services/{created['id']}",
        headers=auth_headers,
        json={"active": False},
    )
    assert resp.status_code == 200
    assert resp.json()["active"] is False
