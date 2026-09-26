"""Signup and login routes. Request validation and persistence come in the auth phase."""

from fastapi import APIRouter, HTTPException, status

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/signup", status_code=status.HTTP_501_NOT_IMPLEMENTED)
def signup() -> None:
    """Placeholder: create a user after validating and hashing the password."""
    raise HTTPException(status_code=501, detail="Signup is not implemented yet")


@router.post("/login", status_code=status.HTTP_501_NOT_IMPLEMENTED)
def login() -> None:
    """Placeholder: verify credentials and return a JWT access token."""
    raise HTTPException(status_code=501, detail="Login is not implemented yet")
