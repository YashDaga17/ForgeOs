from fastapi.testclient import TestClient

from app.main import app


def test_loopback_frontend_ports_are_allowed() -> None:
    client = TestClient(app)

    response = client.options(
        "/api/analyze",
        headers={
            "Origin": "http://127.0.0.1:3001",
            "Access-Control-Request-Method": "POST",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://127.0.0.1:3001"


def test_external_origins_are_not_allowed() -> None:
    client = TestClient(app)

    response = client.options(
        "/api/analyze",
        headers={
            "Origin": "https://untrusted.example",
            "Access-Control-Request-Method": "POST",
        },
    )

    assert response.status_code == 400
