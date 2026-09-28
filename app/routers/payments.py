from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload

from app.dependencies import DbSession, get_current_user
from app.models import Booking, Payment, User, WebhookEvent
from app.routers.bookings import get_owned_booking
from app.schemas import PaymentCreate, PaymentResponse, WebhookPayload, WebhookResponse

router = APIRouter(prefix="/payments", tags=["payments"])


def set_payment_state(payment: Payment, outcome: str) -> None:
    if payment.status not in {"PENDING", outcome}:
        raise HTTPException(status_code=409, detail=f"Payment is already {payment.status}")
    payment.status = outcome
    payment.booking.status = "CONFIRMED" if outcome == "SUCCESS" else "FAILED"


@router.post("/", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
def create_payment(payload: PaymentCreate, db: DbSession, current_user: Annotated[User, Depends(get_current_user)]) -> Payment:
    booking = get_owned_booking(payload.booking_id, db, current_user)
    if booking.status != "PENDING":
        raise HTTPException(status_code=409, detail=f"Booking is {booking.status} and cannot be paid")
    if booking.payment is not None:
        raise HTTPException(status_code=409, detail="A payment already exists for this booking")
    payment = Payment(booking=booking, amount=booking.amount, status="PENDING", provider_reference=f"sim_{uuid4().hex}")
    db.add(payment)
    set_payment_state(payment, payload.outcome)
    db.commit()
    db.refresh(payment)
    return payment


@router.post("/webhook/", response_model=WebhookResponse)
def payment_webhook(payload: WebhookPayload, db: DbSession) -> WebhookResponse:
    existing_event = db.scalar(select(WebhookEvent).where(WebhookEvent.event_id == payload.event_id).options(selectinload(WebhookEvent.payment)))
    if existing_event is not None:
        return WebhookResponse(processed=False, duplicate=True, payment=existing_event.payment)

    payment: Payment | None = None
    if payload.payment_id is not None:
        payment = db.scalar(select(Payment).where(Payment.id == payload.payment_id).options(selectinload(Payment.booking)))
    if payment is None and payload.provider_reference:
        payment = db.scalar(select(Payment).where(Payment.provider_reference == payload.provider_reference).options(selectinload(Payment.booking)))
    if payment is None and payload.booking_id is not None:
        payment = db.scalar(select(Payment).where(Payment.booking_id == payload.booking_id).options(selectinload(Payment.booking)))
    if payment is None and payload.payment_id is not None:
        raise HTTPException(status_code=404, detail="Payment not found")
    if payment is None and payload.provider_reference:
        raise HTTPException(status_code=404, detail="Payment not found")
    if payment is None and payload.booking_id is None:
        raise HTTPException(status_code=404, detail="Payment not found")

    if payment is not None and payload.provider_reference is not None and payment.provider_reference != payload.provider_reference:
        raise HTTPException(status_code=409, detail="Payment and provider reference do not match")

    if payment is None:
        booking = db.get(Booking, payload.booking_id)
        if booking is None:
            raise HTTPException(status_code=404, detail="Booking not found")
        if booking.status == "CANCELLED":
            raise HTTPException(status_code=409, detail="Cancelled bookings cannot receive payment events")
        payment = Payment(booking_id=booking.id, amount=booking.amount, status="PENDING", provider_reference=payload.provider_reference or f"wh_{payload.event_id}")
        db.add(payment)
        db.flush()
    elif payload.booking_id is not None and payment.booking_id != payload.booking_id:
        raise HTTPException(status_code=409, detail="Payment and booking do not match")

    set_payment_state(payment, payload.status)
    db.add(WebhookEvent(event_id=payload.event_id, payment_id=payment.id, status=payload.status))
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        duplicate = db.scalar(select(WebhookEvent).where(WebhookEvent.event_id == payload.event_id).options(selectinload(WebhookEvent.payment)))
        if duplicate is not None:
            return WebhookResponse(processed=False, duplicate=True, payment=duplicate.payment)
        raise HTTPException(status_code=409, detail="Webhook could not be applied") from exc
    db.refresh(payment)
    return WebhookResponse(processed=True, duplicate=False, payment=payment)
