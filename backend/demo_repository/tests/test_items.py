from __future__ import annotations


def test_get_items(client):
    response = client.get("/items")

    assert response.status_code == 200
    assert len(response.json()) >= 2


def test_create_item(client):
    response = client.post(
        "/items",
        json={"id": 99, "name": "Test Relay", "price": 12.5},
    )

    assert response.status_code == 201
    assert response.json()["name"] == "Test Relay"


def test_get_item_not_found(client):
    response = client.get("/items/999")

    assert response.status_code == 404


def test_update_item(client):
    response = client.put(
        "/items/1",
        json={"id": 1, "name": "Updated Beacon", "price": 50.0},
    )

    assert response.status_code == 200
    assert response.json()["name"] == "Updated Beacon"


def test_delete_item(client):
    response = client.delete("/items/2")

    assert response.status_code == 200
    assert response.json() == {"deleted": True}

