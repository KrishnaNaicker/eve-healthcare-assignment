"""Small API tests; feature tests will be added as each route is implemented."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_check() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_centre_pagination_parameters_are_bounded() -> None:
    response = client.get("/centres/?offset=-1")

    assert response.status_code == 422
