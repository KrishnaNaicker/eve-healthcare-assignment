# EVE Healthcare Booking API

A small FastAPI backend for diagnostic-centre test bookings and a simulated payment provider. It implements the assignment flow with PostgreSQL, SQLAlchemy, Pydantic validation, JWT authentication, secure password hashing, Alembic migrations, Docker Compose, structured logs, pagination, and integration tests.

## Architecture

```text
app/main.py                 application and router registration
app/config.py               environment-backed settings
app/database.py             SQLAlchemy engine, Base, and request sessions
app/models.py               relational database tables and relationships
app/schemas.py              request validation and response shapes
app/security.py             password hashing and JWT creation/decoding
app/dependencies.py         database/auth/admin FastAPI dependencies
app/routers/auth.py         signup, login, current-user endpoint
app/routers/centres.py      centre/test CRUD and public retrieval
app/routers/bookings.py     authenticated booking operations
app/routers/payments.py     simulated payment and webhook processing
alembic/                    PostgreSQL schema migration
tests/test_api.py           reproducible API integration tests
```

The request flow is route -> Pydantic validation -> authentication/authorization dependency -> SQLAlchemy session -> PostgreSQL -> response.

## Data model

- `users` stores email, display name, Argon2 password hash, and `USER`/`ADMIN` role.
- `diagnostic_centres` stores a unique name, location, and active flag.
- `diagnostic_tests` belongs to one centre and stores a decimal price. A centre/test-name unique constraint prevents duplicate offerings.
- `bookings` belongs to one user, test, and centre. It stores appointment time and a price snapshot.
- `payments` has one row per booking, a decimal amount, provider reference, and `PENDING`, `SUCCESS`, or `FAILED` status.
- `webhook_events` stores each provider event ID once; its unique constraint is the database-level idempotency guard.

The booking lifecycle is `PENDING` -> `CONFIRMED` or `FAILED` after payment. A pending or confirmed booking can be `CANCELLED`; final states cannot be paid again.

## Authentication and authorization

Signup stores only a one-way Argon2 password hash. Login verifies it and returns a signed JWT whose `sub` claim contains the user ID. Protected routes use the bearer token, load the user from the database, and reject invalid or expired tokens with `401`.

Centre/test management requires the `ADMIN` role. Normal users can browse catalog data, create bookings, read their own bookings, pay for them, and cancel eligible bookings. Another user's booking returns `403`.

For local development, set `ADMIN_EMAIL` before signup; a signup using that email receives the admin role. In production, role assignment should use a controlled admin workflow.

## Payment and webhook lifecycle

`POST /payments/` creates one simulated payment for a pending booking. `SUCCESS` changes both payment and booking to success/confirmed; `FAILED` changes both to failed. A unique `booking_id` prevents duplicate payments.

`POST /payments/webhook/` accepts an event ID, status, and a payment, provider reference, or booking identifier. It resolves the payment, validates the relationship, applies only valid transitions, and inserts the event ID in the same transaction. A repeated event returns the existing result with `duplicate: true` and performs no side effects.

## API endpoints

| Method | Path | Auth | Purpose |
| --- | --- | --- | --- |
| POST | `/auth/signup` | public | Register a user |
| POST | `/auth/login` | public | Return a JWT bearer token |
| GET | `/auth/me` | user | Return the authenticated user |
| GET | `/centres/` | public | Paginated active centres and tests |
| POST | `/centres/` | admin | Create a centre |
| GET | `/centres/{centre_id}` | public | Retrieve a centre |
| PATCH/DELETE | `/centres/{centre_id}` | admin | Update/deactivate a centre |
| GET | `/centres/{centre_id}/tests` | public | List tests at a centre |
| POST | `/centres/{centre_id}/tests` | admin | Add a test offering |
| GET | `/tests/` | public | List tests, optionally by centre |
| PATCH/DELETE | `/tests/{test_id}` | admin | Update/deactivate a test |
| POST | `/bookings/` | user | Create a future appointment booking |
| GET | `/bookings/` | user | List the user's bookings |
| GET/PATCH | `/bookings/{booking_id}` | owner/admin | Read or cancel a booking |
| POST | `/payments/` | owner/admin | Simulate `SUCCESS` or `FAILED` payment |
| POST | `/payments/webhook/` | provider | Process an idempotent status event |
| GET | `/health` | public | Process health check |

Swagger UI is available at `/docs`; the OpenAPI schema is at `/openapi.json`.

## Configuration

Copy `.env.example` to `.env` for local non-Docker runs:

```text
DATABASE_URL=postgresql+psycopg://eve_user:eve_password@localhost:5432/eve_healthcare
JWT_SECRET_KEY=at-least-32-random-characters
JWT_ACCESS_TOKEN_MINUTES=30
ADMIN_EMAIL=admin@example.com
```

Never commit `.env` or real secrets. Compose supplies the database service URL to the API container.

## Run with Docker Compose

```bash
docker compose up --build
```

If Docker Desktop exposes the legacy command on your machine, use `docker-compose up --build` instead.

The database health check runs first. The API container applies `alembic upgrade head`, then starts Uvicorn on `http://localhost:8000`. Open `http://localhost:8000/docs`. Stop with `docker compose down`; use `docker compose down -v` only when you intentionally want to remove the local database volume.

## Run locally without Docker

Create a PostgreSQL database matching `DATABASE_URL`, activate a Python 3.12 virtual environment, then run:

```bash
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

## Tests

The suite uses an isolated in-memory SQLite database and FastAPI's `TestClient`, so it is deterministic and does not require PostgreSQL:

```bash
pytest -q
```

It covers signup/login, duplicate accounts, protected routes, admin catalog operations, validation, bookings, ownership checks, invalid IDs, successful and failed payments, invalid transitions, webhook creation, duplicate delivery, and unknown resources.

## Assumptions and design decisions

- A test offering belongs to one centre; bookings store both foreign keys and creation verifies they match.
- Money uses `NUMERIC(10, 2)`/`Decimal`, not binary floating point.
- Webhook events are provider input and do not require a user JWT, but they must identify a real payment or booking.
- Docker, Swagger, tests, structured JSON logging, pagination, and migration support are included practical bonus items. Redis, Celery, rate limiting, and external gateways are intentionally excluded.

## Final checklist

- Authentication: signup, login, JWT, hashing, validation, protected routes
- Centres/tests: public retrieval, admin management, pricing, uniqueness constraints
- Bookings: authenticated creation, ownership, appointment time, amount snapshot, state transitions
- Payments: simulated success/failure and consistent booking updates
- Webhook: validation, database-backed idempotency, duplicate safety, invalid-resource handling
- Documentation: README, OpenAPI, `.env.example`, Docker Compose, Alembic migration
- Tests: 7 integration tests passing

With more time, I would add refresh tokens, a dedicated admin provisioning command, richer audit logs, database-level enum/check constraints, and a PostgreSQL CI service.
