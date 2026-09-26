"""Simulated payment and idempotent provider webhook routes."""

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/payments", tags=["payments"])


@router.post("/", status_code=501)
def create_payment() -> None:
    """Placeholder: simulate payment and update the linked booking state."""
    raise HTTPException(status_code=501, detail="Payments are not implemented yet")


@router.post("/webhook/", status_code=501)
def payment_webhook() -> None:
    """Placeholder: deduplicate event IDs; transient failures should return 5xx for retry."""
    raise HTTPException(status_code=501, detail="Payment webhook is not implemented yet")
