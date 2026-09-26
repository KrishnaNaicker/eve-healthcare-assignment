# EVE Healthcare Booking API

Backend assignment scaffold for diagnostic-centre test bookings and simulated payments.
Core behavior is intentionally being implemented step by step as a learning exercise.

## Stack

- Python, FastAPI, Pydantic, SQLAlchemy, PostgreSQL
- JWT authentication (planned)
- Docker Compose for the API and PostgreSQL
- pytest and FastAPI's generated OpenAPI/Swagger UI

## Current progress

This is an in-progress learning project, not a finished assignment submission.

| Area | Progress |
| --- | --- |
| App scaffold, root/health routes, JSON logging | Started |
| Environment settings and SQLAlchemy connection/session setup | Scaffolded |
| Docker Compose with PostgreSQL and API | Scaffolded |
| Swagger/OpenAPI and paginated centre-list inputs | Scaffolded |
| Starter API tests | Written, not yet run |
| SQLAlchemy data models | In progress; the centre model draft still needs correction |
| Signup, login, JWT, database-backed centres/tests, bookings, payments, webhook | Not implemented |

The feature routers are placeholders, and several endpoints return `501 Not Implemented`.
The centre-list route currently returns an empty placeholder response rather than querying PostgreSQL.

## Run locally with Docker

1. Install Docker Desktop and start it.
2. Copy `.env.example` to `.env` and set a private `JWT_SECRET_KEY` for your machine.
3. Run `docker compose up --build`.
4. Open `http://localhost:8000/docs` for Swagger UI or `http://localhost:8000/health`.
5. Stop with `docker compose down`. Add `-v` only if you intend to remove the local database volume.

## Run without Docker

1. Create and activate a virtual environment.
2. Install dependencies with `pip install -r requirements.txt`.
3. Copy `.env.example` to `.env` and make sure PostgreSQL is running with the configured database.
4. Start the API using `uvicorn app.main:app --reload`.

## Planned data model

`User` owns `Booking` records. A `DiagnosticCentre` offers `DiagnosticTest` records with a
price. A `Booking` references the selected offered test and stores an amount snapshot and
appointment time. `Payment` references a booking. A separate webhook-event record will
store unique provider event IDs so duplicate deliveries can be safely ignored while still
allowing multiple events for one payment.

## Planned endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| POST | `/auth/signup` | Create an account |
| POST | `/auth/login` | Obtain a JWT |
| GET | `/centres/?offset=0&limit=20` | Browse centres with bounded pagination |
| GET | `/centres/{centre_id}/tests` | List tests and prices at a centre |
| POST | `/bookings/` | Create an authenticated booking |
| GET | `/bookings/{booking_id}` | Read an owned booking |
| POST | `/payments/` | Simulate payment processing |
| POST | `/payments/webhook/` | Process a provider status event idempotently |

## Design notes

- FastAPI supplies interactive OpenAPI documentation at `/docs`.
- The app writes JSON-formatted logs to stdout for Docker log collection.
- Transient webhook processing failures should return a server error so a provider can retry;
  a unique event ID and database transaction will prevent duplicate side effects.
- Redis, Celery, and rate limiting are intentionally omitted from this small service.

## Tests

Run `pytest`. The current starter tests cover the health route and pagination validation;
they have not yet been run. Tests for authentication, booking, payment, webhook,
idempotency, and authorization will be added as those features are implemented.

## Assumptions and future improvements

- A diagnostic test's price is attached to the centre's offered test.
- Booking amount is copied when the booking is created so later price changes do not rewrite history.
- With more time, add schema migrations, stronger production secret management, and broader integration tests.
