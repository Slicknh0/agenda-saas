def _create_service(client, auth_headers, duration=60):
    resp = client.post(
        "/services",
        headers=auth_headers,
        json={"name": "Consulta", "duration_minutes": duration, "price_cents": 10000},
    )
    return resp.json()


def test_public_can_list_services_without_auth(client, auth_headers, registered_tenant):
    _create_service(client, auth_headers)
    resp = client.get(f"/public/{registered_tenant['slug']}/services")
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_public_can_book_appointment(client, auth_headers, registered_tenant):
    service = _create_service(client, auth_headers)
    resp = client.post(
        f"/public/{registered_tenant['slug']}/book",
        json={
            "service_id": service["id"],
            "client_name": "Maria",
            "client_contact": "11999990000",
            "starts_at": "2027-01-10T14:00:00",
        },
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["status"] == "scheduled"
    assert body["duration_minutes"] == 60


def test_overlapping_booking_is_rejected(client, auth_headers, registered_tenant):
    service = _create_service(client, auth_headers, duration=60)
    slug = registered_tenant["slug"]

    first = client.post(
        f"/public/{slug}/book",
        json={
            "service_id": service["id"],
            "client_name": "Maria",
            "client_contact": "11999990000",
            "starts_at": "2027-01-10T14:00:00",
        },
    )
    assert first.status_code == 201

    # starts 30min into the first appointment's 60min slot -> overlaps
    second = client.post(
        f"/public/{slug}/book",
        json={
            "service_id": service["id"],
            "client_name": "Joao",
            "client_contact": "11988880000",
            "starts_at": "2027-01-10T14:30:00",
        },
    )
    assert second.status_code == 409


def test_back_to_back_booking_is_allowed(client, auth_headers, registered_tenant):
    service = _create_service(client, auth_headers, duration=60)
    slug = registered_tenant["slug"]

    first = client.post(
        f"/public/{slug}/book",
        json={
            "service_id": service["id"],
            "client_name": "Maria",
            "client_contact": "11999990000",
            "starts_at": "2027-01-10T14:00:00",
        },
    )
    assert first.status_code == 201

    # starts exactly when the first one ends -> no overlap
    second = client.post(
        f"/public/{slug}/book",
        json={
            "service_id": service["id"],
            "client_name": "Joao",
            "client_contact": "11988880000",
            "starts_at": "2027-01-10T15:00:00",
        },
    )
    assert second.status_code == 201
