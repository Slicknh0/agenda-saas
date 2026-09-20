def _create_service(client, auth_headers, name):
    return client.post(
        "/services",
        headers=auth_headers,
        json={"name": name, "duration_minutes": 30, "price_cents": 1000},
    )


def test_free_plan_blocks_fourth_active_service(client, auth_headers):
    for i in range(3):
        resp = _create_service(client, auth_headers, f"Servico {i}")
        assert resp.status_code == 201

    resp = _create_service(client, auth_headers, "Servico 4")
    assert resp.status_code == 402
    assert "free" in resp.json()["detail"].lower()


def test_deactivating_a_service_frees_up_the_limit(client, auth_headers):
    ids = []
    for i in range(3):
        resp = _create_service(client, auth_headers, f"Servico {i}")
        ids.append(resp.json()["id"])

    client.patch(f"/services/{ids[0]}", headers=auth_headers, json={"active": False})

    resp = _create_service(client, auth_headers, "Servico novo")
    assert resp.status_code == 201
