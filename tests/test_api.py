from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models import Payment, WebhookEvent

TEST_ENGINE = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
Base.metadata.create_all(TEST_ENGINE)


@pytest.fixture()
def client():
    Base.metadata.drop_all(TEST_ENGINE)
    Base.metadata.create_all(TEST_ENGINE)

    def override_get_db():
        with Session(TEST_ENGINE) as db:
            yield db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def signup(client: TestClient, email: str = "user@example.com") -> dict:
    response = client.post("/auth/signup", json={"email": email, "full_name": "Test User", "password": "password123"})
    assert response.status_code == 201, response.text
    return response.json()


def login(client: TestClient, email: str = "user@example.com") -> dict:
    response = client.post("/auth/login", json={"email": email, "password": "password123"})
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def seed_catalog(client: TestClient, admin_headers: dict) -> tuple[int, int]:
    centre_response = client.post("/centres/", headers=admin_headers, json={"name": "Central Diagnostics", "location": "Bengaluru"})
    assert centre_response.status_code == 201, centre_response.text
    centre_id = centre_response.json()["id"]
    test_response = client.post(f"/centres/{centre_id}/tests", headers=admin_headers, json={"name": "CBC", "description": "Complete blood count", "price": "650.00"})
    assert test_response.status_code == 201, test_response.text
    return centre_id, test_response.json()["id"]


def admin_login(client: TestClient) -> dict:
    from app.config import settings

    settings.admin_email = "admin@example.com"
    signup(client, "admin@example.com")
    signup(client)
    return login(client, "admin@example.com")


def make_booking(client: TestClient, headers: dict, test_id: int) -> dict:
    response = client.post("/bookings/", headers=headers, json={"test_id": test_id, "appointment_at": (datetime.now(UTC) + timedelta(days=1)).isoformat()})
    assert response.status_code == 201, response.text
    return response.json()


def test_health_and_root(client: TestClient):
    assert client.get("/health").json() == {"status": "ok"}
    assert client.get("/").status_code == 200


def test_signup_duplicate_login_and_protected_route(client: TestClient):
    signup(client)
    assert client.post("/auth/signup", json={"email": "user@example.com", "full_name": "Other User", "password": "password123"}).status_code == 409
    assert client.post("/auth/login", json={"email": "user@example.com", "password": "wrongpassword"}).status_code == 401
    assert client.get("/auth/me").status_code == 401
    assert client.get("/auth/me", headers=login(client)).status_code == 200


def test_admin_catalog_crud_and_public_retrieval(client: TestClient):
    admin_headers = admin_login(client)
    centre_id, test_id = seed_catalog(client, admin_headers)
    listing = client.get("/centres/")
    assert listing.status_code == 200 and listing.json()["total"] == 1
    assert client.get(f"/centres/{centre_id}/tests").json()[0]["id"] == test_id
    assert client.post("/centres/", headers=login(client), json={"name": "Nope", "location": "Nowhere"}).status_code == 403


def test_booking_payment_and_authorization(client: TestClient):
    admin_headers = admin_login(client)
    _, test_id = seed_catalog(client, admin_headers)
    user_headers = login(client)
    booking = make_booking(client, user_headers, test_id)
    assert booking["status"] == "PENDING"
    assert client.get(f"/bookings/{booking['id']}", headers=user_headers).status_code == 200
    signup(client, "second@example.com")
    assert client.get(f"/bookings/{booking['id']}", headers=login(client, "second@example.com")).status_code == 403
    payment = client.post("/payments/", headers=user_headers, json={"booking_id": booking["id"], "outcome": "SUCCESS"})
    assert payment.status_code == 201 and payment.json()["status"] == "SUCCESS"
    assert client.get(f"/bookings/{booking['id']}", headers=user_headers).json()["status"] == "CONFIRMED"
    assert client.post("/payments/", headers=user_headers, json={"booking_id": booking["id"], "outcome": "FAILED"}).status_code == 409


def test_failed_payment_and_cancellation(client: TestClient):
    admin_headers = admin_login(client)
    _, test_id = seed_catalog(client, admin_headers)
    headers = login(client)
    booking = make_booking(client, headers, test_id)
    payment = client.post("/payments/", headers=headers, json={"booking_id": booking["id"], "outcome": "FAILED"})
    assert payment.status_code == 201 and payment.json()["status"] == "FAILED"
    assert client.get(f"/bookings/{booking['id']}", headers=headers).json()["status"] == "FAILED"
    assert client.patch(f"/bookings/{booking['id']}", headers=headers, json={"status": "CANCELLED"}).status_code == 409


def test_webhook_is_idempotent_and_rejects_invalid_events(client: TestClient):
    admin_headers = admin_login(client)
    _, test_id = seed_catalog(client, admin_headers)
    headers = login(client)
    booking = make_booking(client, headers, test_id)
    event = {"event_id": "evt_1", "booking_id": booking["id"], "status": "SUCCESS"}
    first = client.post("/payments/webhook/", json=event)
    second = client.post("/payments/webhook/", json=event)
    assert first.status_code == 200 and first.json()["processed"] is True
    assert second.status_code == 200 and second.json()["duplicate"] is True
    with Session(TEST_ENGINE) as db:
        assert db.scalar(select(Payment).where(Payment.booking_id == booking["id"])) is not None
        assert db.scalar(select(WebhookEvent).where(WebhookEvent.event_id == "evt_1")) is not None
    assert client.post("/payments/webhook/", json={"event_id": "bad", "status": "SUCCESS"}).status_code == 422
    assert client.post("/payments/webhook/", json={"event_id": "evt_2", "payment_id": 999, "status": "SUCCESS"}).status_code == 404


def test_validation_and_not_found_cases(client: TestClient):
    signup(client)
    headers = login(client)
    assert client.post("/bookings/", headers=headers, json={"test_id": 999, "appointment_at": "tomorrow"}).status_code == 422
    assert client.get("/bookings/999", headers=headers).status_code == 404
    assert client.get("/centres/999").status_code == 404
