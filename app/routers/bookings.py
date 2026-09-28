from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.dependencies import DbSession, get_current_user
from app.models import Booking, DiagnosticTest, User
from app.schemas import BookingCreate, BookingResponse, BookingStatusUpdate

router = APIRouter(prefix="/bookings", tags=["bookings"])


def get_owned_booking(booking_id: int, db, user: User) -> Booking:
    booking = db.scalar(select(Booking).where(Booking.id == booking_id).options(selectinload(Booking.payment)))
    if booking is None:
        raise HTTPException(status_code=404, detail="Booking not found")
    if booking.user_id != user.id and user.role != "ADMIN":
        raise HTTPException(status_code=403, detail="You cannot access this booking")
    return booking


@router.post("/", response_model=BookingResponse, status_code=status.HTTP_201_CREATED)
def create_booking(payload: BookingCreate, db: DbSession, current_user: Annotated[User, Depends(get_current_user)]) -> Booking:
    appointment = payload.appointment_at.astimezone(UTC)
    if appointment <= datetime.now(UTC):
        raise HTTPException(status_code=422, detail="appointment_at must be in the future")
    test = db.scalar(select(DiagnosticTest).where(DiagnosticTest.id == payload.test_id, DiagnosticTest.is_active.is_(True)).options(selectinload(DiagnosticTest.centre)))
    if test is None or not test.centre.is_active:
        raise HTTPException(status_code=404, detail="Diagnostic test not found")
    booking = Booking(user_id=current_user.id, test_id=test.id, centre_id=test.centre_id, appointment_at=appointment, amount=test.price, status="PENDING")
    db.add(booking)
    db.commit()
    db.refresh(booking)
    return booking


@router.get("/", response_model=list[BookingResponse])
def list_bookings(db: DbSession, current_user: Annotated[User, Depends(get_current_user)], offset: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=100)) -> list[Booking]:
    query = select(Booking).where(Booking.user_id == current_user.id).options(selectinload(Booking.payment)).order_by(Booking.id.desc()).offset(offset).limit(limit)
    return list(db.scalars(query).all())


@router.get("/{booking_id}", response_model=BookingResponse)
def get_booking(booking_id: int, db: DbSession, current_user: Annotated[User, Depends(get_current_user)]) -> Booking:
    return get_owned_booking(booking_id, db, current_user)


@router.patch("/{booking_id}", response_model=BookingResponse)
def cancel_booking(booking_id: int, payload: BookingStatusUpdate, db: DbSession, current_user: Annotated[User, Depends(get_current_user)]) -> Booking:
    booking = get_owned_booking(booking_id, db, current_user)
    if booking.status not in {"PENDING", "CONFIRMED"}:
        raise HTTPException(status_code=409, detail=f"Booking cannot be cancelled from {booking.status} state")
    booking.status = payload.status
    db.commit()
    db.refresh(booking)
    return booking
