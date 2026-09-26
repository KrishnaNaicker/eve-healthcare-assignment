"""Authenticated booking routes will be implemented in the booking phase."""

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/bookings", tags=["bookings"])


@router.post("/", status_code=501)
def create_booking() -> None:
    """Placeholder: create a booking for the authenticated patient."""
    raise HTTPException(status_code=501, detail="Booking creation is not implemented yet")


@router.get("/{booking_id}")
def get_booking(booking_id: int) -> None:
    """Placeholder: retrieve a booking after checking ownership."""
    raise HTTPException(status_code=501, detail="Booking lookup is not implemented yet")
