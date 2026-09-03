"""Track latest applied telemetry per source entity.

Revision ID: 20260903_02
Revises: 20260903_01
Create Date: 2026-09-03
"""
from alembic import op
import sqlalchemy as sa

revision = "20260903_02"
down_revision = "20260903_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if "telemetry_entity_states" in inspector.get_table_names():
        return
    op.create_table(
        "telemetry_entity_states",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("source_id", sa.String(80), nullable=False),
        sa.Column("source_type", sa.String(40), nullable=False),
        sa.Column("entity_key", sa.String(200), nullable=False),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source_event_id", sa.String(100), nullable=False),
        sa.UniqueConstraint("source_id", "source_type", "entity_key", name="uq_telemetry_entity_state"),
    )
    op.create_index("ix_telemetry_entity_states_source_id", "telemetry_entity_states", ["source_id"])
    op.create_index("ix_telemetry_entity_states_source_type", "telemetry_entity_states", ["source_type"])


def downgrade() -> None:
    op.drop_table("telemetry_entity_states")
