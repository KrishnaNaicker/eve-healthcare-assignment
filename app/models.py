"""Database model TODOs (the SQLAlchemy tables will be written with you).

Planned tables:
- User: login identity and password hash.
- DiagnosticCentre: centre name and location.
- DiagnosticTest: centre, test name, and price (an offered test belongs to a centre).
- Booking: patient, offered test, appointment time, amount snapshot, and status.
- Payment: booking, result, and unique provider event ID for webhook idempotency.

Relationships use primary keys and foreign keys. A unique webhook event ID lets a
duplicate delivery be detected safely. We will turn this outline into real models
when we study SQLAlchemy and relational keys.
"""
