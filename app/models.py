from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Index, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(120))
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20), default="USER")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    bookings: Mapped[list["Booking"]] = relationship(back_populates="user")


class DiagnosticCentre(Base):
    __tablename__ = "diagnostic_centres"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    location: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    tests: Mapped[list["DiagnosticTest"]] = relationship(back_populates="centre", cascade="all, delete-orphan")


class DiagnosticTest(Base):
    __tablename__ = "diagnostic_tests"
    __table_args__ = (UniqueConstraint("centre_id", "name", name="uq_test_centre_name"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    centre_id: Mapped[int] = mapped_column(ForeignKey("diagnostic_centres.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(120))
    description: Mapped[str | None] = mapped_column(Text(), nullable=True)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    is_active: Mapped[bool] = mapped_column(default=True, index=True)
    centre: Mapped[DiagnosticCentre] = relationship(back_populates="tests")
    bookings: Mapped[list["Booking"]] = relationship(back_populates="test")


class Booking(Base):
    __tablename__ = "bookings"
    __table_args__ = (Index("ix_bookings_user_created", "user_id", "created_at"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), index=True)
    test_id: Mapped[int] = mapped_column(ForeignKey("diagnostic_tests.id", ondelete="RESTRICT"), index=True)
    centre_id: Mapped[int] = mapped_column(ForeignKey("diagnostic_centres.id", ondelete="RESTRICT"), index=True)
    appointment_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    status: Mapped[str] = mapped_column(String(20), default="PENDING", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    user: Mapped[User] = relationship(back_populates="bookings")
    test: Mapped[DiagnosticTest] = relationship(back_populates="bookings")
    centre: Mapped[DiagnosticCentre] = relationship()
    payment: Mapped["Payment | None"] = relationship(back_populates="booking", uselist=False, cascade="all, delete-orphan")


class Payment(Base):
    __tablename__ = "payments"
    id: Mapped[int] = mapped_column(primary_key=True)
    booking_id: Mapped[int] = mapped_column(ForeignKey("bookings.id", ondelete="CASCADE"), unique=True, index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    status: Mapped[str] = mapped_column(String(20), default="PENDING", index=True)
    provider_reference: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    booking: Mapped[Booking] = relationship(back_populates="payment")
    webhook_events: Mapped[list["WebhookEvent"]] = relationship(back_populates="payment")


class WebhookEvent(Base):
    __tablename__ = "webhook_events"
    id: Mapped[int] = mapped_column(primary_key=True)
    event_id: Mapped[str] = mapped_column(String(160), unique=True, index=True)
    payment_id: Mapped[int] = mapped_column(ForeignKey("payments.id", ondelete="CASCADE"))
    status: Mapped[str] = mapped_column(String(20))
    processed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    payment: Mapped[Payment] = relationship(back_populates="webhook_events")
