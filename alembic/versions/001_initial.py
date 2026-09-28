"""Create assignment tables."""

from alembic import op
import sqlalchemy as sa

revision = "001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table("users", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("email", sa.String(320), nullable=False), sa.Column("full_name", sa.String(120), nullable=False), sa.Column("password_hash", sa.String(255), nullable=False), sa.Column("role", sa.String(20), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_table("diagnostic_centres", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("name", sa.String(120), nullable=False), sa.Column("location", sa.String(255), nullable=False), sa.Column("is_active", sa.Boolean(), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))
    op.create_index("ix_diagnostic_centres_name", "diagnostic_centres", ["name"], unique=True)
    op.create_index("ix_diagnostic_centres_is_active", "diagnostic_centres", ["is_active"])
    op.create_table("diagnostic_tests", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("centre_id", sa.Integer(), nullable=False), sa.Column("name", sa.String(120), nullable=False), sa.Column("description", sa.Text()), sa.Column("price", sa.Numeric(10, 2), nullable=False), sa.Column("is_active", sa.Boolean(), nullable=False), sa.ForeignKeyConstraint(["centre_id"], ["diagnostic_centres.id"], ondelete="CASCADE"), sa.UniqueConstraint("centre_id", "name", name="uq_test_centre_name"))
    op.create_index("ix_diagnostic_tests_centre_id", "diagnostic_tests", ["centre_id"])
    op.create_index("ix_diagnostic_tests_is_active", "diagnostic_tests", ["is_active"])
    op.create_table("bookings", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False), sa.Column("test_id", sa.Integer(), sa.ForeignKey("diagnostic_tests.id", ondelete="RESTRICT"), nullable=False), sa.Column("centre_id", sa.Integer(), sa.ForeignKey("diagnostic_centres.id", ondelete="RESTRICT"), nullable=False), sa.Column("appointment_at", sa.DateTime(timezone=True), nullable=False), sa.Column("amount", sa.Numeric(10, 2), nullable=False), sa.Column("status", sa.String(20), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))
    op.create_index("ix_bookings_user_id", "bookings", ["user_id"])
    op.create_index("ix_bookings_test_id", "bookings", ["test_id"])
    op.create_index("ix_bookings_centre_id", "bookings", ["centre_id"])
    op.create_index("ix_bookings_appointment_at", "bookings", ["appointment_at"])
    op.create_index("ix_bookings_status", "bookings", ["status"])
    op.create_index("ix_bookings_user_created", "bookings", ["user_id", "created_at"])
    op.create_table("payments", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("booking_id", sa.Integer(), sa.ForeignKey("bookings.id", ondelete="CASCADE"), nullable=False), sa.Column("amount", sa.Numeric(10, 2), nullable=False), sa.Column("status", sa.String(20), nullable=False), sa.Column("provider_reference", sa.String(120), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False), sa.UniqueConstraint("booking_id"), sa.UniqueConstraint("provider_reference"))
    op.create_index("ix_payments_booking_id", "payments", ["booking_id"])
    op.create_index("ix_payments_status", "payments", ["status"])
    op.create_index("ix_payments_provider_reference", "payments", ["provider_reference"])
    op.create_table("webhook_events", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("event_id", sa.String(160), nullable=False), sa.Column("payment_id", sa.Integer(), sa.ForeignKey("payments.id", ondelete="CASCADE"), nullable=False), sa.Column("status", sa.String(20), nullable=False), sa.Column("processed_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False), sa.UniqueConstraint("event_id"))
    op.create_index("ix_webhook_events_event_id", "webhook_events", ["event_id"])


def downgrade() -> None:
    op.drop_table("webhook_events")
    op.drop_table("payments")
    op.drop_table("bookings")
    op.drop_table("diagnostic_tests")
    op.drop_table("diagnostic_centres")
    op.drop_table("users")
