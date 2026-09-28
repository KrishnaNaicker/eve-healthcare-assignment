from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator


class UserCreate(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=2, max_length=120)
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: EmailStr
    full_name: str
    role: str


class CentreCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    location: str = Field(min_length=2, max_length=255)


class CentreUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    location: str | None = Field(default=None, min_length=2, max_length=255)
    is_active: bool | None = None


class TestCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    description: str | None = Field(default=None, max_length=1000)
    price: Decimal = Field(gt=0, max_digits=10, decimal_places=2)


class TestUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    description: str | None = Field(default=None, max_length=1000)
    price: Decimal | None = Field(default=None, gt=0, max_digits=10, decimal_places=2)
    is_active: bool | None = None


class TestResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    centre_id: int
    name: str
    description: str | None
    price: Decimal
    is_active: bool


class CentreResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    location: str
    is_active: bool
    tests: list[TestResponse] = Field(default_factory=list)


class PaginatedCentres(BaseModel):
    items: list[CentreResponse]
    offset: int
    limit: int
    total: int


class BookingCreate(BaseModel):
    test_id: int = Field(gt=0)
    appointment_at: datetime

    @field_validator("appointment_at")
    @classmethod
    def appointment_must_have_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("appointment_at must include a timezone")
        return value


class BookingStatusUpdate(BaseModel):
    status: Literal["CANCELLED"]


class PaymentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    booking_id: int
    amount: Decimal
    status: Literal["PENDING", "SUCCESS", "FAILED"]
    provider_reference: str


class BookingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int
    test_id: int
    centre_id: int
    appointment_at: datetime
    amount: Decimal
    status: Literal["PENDING", "CONFIRMED", "FAILED", "CANCELLED"]
    payment: PaymentResponse | None = None


class PaymentCreate(BaseModel):
    booking_id: int = Field(gt=0)
    outcome: Literal["SUCCESS", "FAILED"]


class WebhookPayload(BaseModel):
    event_id: str = Field(min_length=3, max_length=160)
    status: Literal["SUCCESS", "FAILED"]
    payment_id: int | None = Field(default=None, gt=0)
    provider_reference: str | None = Field(default=None, min_length=3, max_length=120)
    booking_id: int | None = Field(default=None, gt=0)

    @model_validator(mode="after")
    def require_reference(self):
        if not any((self.payment_id, self.provider_reference, self.booking_id)):
            raise ValueError("payment_id, provider_reference, or booking_id is required")
        return self


class WebhookResponse(BaseModel):
    processed: bool
    duplicate: bool
    payment: PaymentResponse
