"""Persist investment-option metadata and optimisation runs.

Revision ID: 20260903_03
Revises: 20260903_02
Create Date: 2026-09-03
"""
from alembic import op
import sqlalchemy as sa

revision = "20260903_03"
down_revision = "20260903_02"
branch_labels = None
depends_on = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    option_columns = {column["name"] for column in inspector.get_columns("investment_options")}
    with op.batch_alter_table("investment_options") as batch:
        if "description" not in option_columns:
            batch.add_column(sa.Column("description", sa.Text(), nullable=True))
        if "affected_asset_ids" not in option_columns:
            batch.add_column(sa.Column("affected_asset_ids", sa.JSON(), nullable=True))
        if "affected_control_ids" not in option_columns:
            batch.add_column(sa.Column("affected_control_ids", sa.JSON(), nullable=True))
        if "dependencies" not in option_columns:
            batch.add_column(sa.Column("dependencies", sa.JSON(), nullable=True))
        if "exclusions" not in option_columns:
            batch.add_column(sa.Column("exclusions", sa.JSON(), nullable=True))
    if "optimization_runs" not in inspector.get_table_names():
        op.create_table(
            "optimization_runs",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("budget", sa.Float(), nullable=False),
            sa.Column("selected_investments", sa.JSON(), nullable=False),
            sa.Column("total_cost", sa.Float(), nullable=False),
            sa.Column("estimated_risk_reduction", sa.Float(), nullable=False),
            sa.Column("residual_risk", sa.Float(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        )
        op.create_index("ix_optimization_runs_created_at", "optimization_runs", ["created_at"])


def downgrade() -> None:
    op.drop_table("optimization_runs")
