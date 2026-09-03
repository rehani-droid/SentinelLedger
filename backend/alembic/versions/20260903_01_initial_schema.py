"""Initial SentinelLedger schema and persisted risk projections.

Revision ID: 20260903_01
Revises:
Create Date: 2026-09-03
"""
from alembic import op
import sqlalchemy as sa

revision = "20260903_01"
down_revision = None
branch_labels = None
depends_on = None

def _has_table(name: str) -> bool:
    return name in sa.inspect(op.get_bind()).get_table_names()

def upgrade() -> None:
    if not _has_table("business_units"):
        op.create_table("business_units", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("name", sa.String(120), nullable=False, unique=True))
    if not _has_table("roles"):
        op.create_table("roles", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("name", sa.String(40), nullable=False, unique=True))
    if not _has_table("assets"):
        op.create_table("assets", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("name", sa.String(160), nullable=False, unique=True), sa.Column("asset_type", sa.String(50), nullable=False), sa.Column("business_unit_id", sa.Integer(), sa.ForeignKey("business_units.id")), sa.Column("criticality", sa.Float(), nullable=False), sa.Column("data_sensitivity", sa.Float(), nullable=False), sa.Column("internet_exposed", sa.Boolean(), nullable=False, server_default=sa.false()), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))
        op.create_index("ix_assets_name", "assets", ["name"]); op.create_index("ix_assets_business_unit_id", "assets", ["business_unit_id"])
    if not _has_table("applications"):
        op.create_table("applications", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("name", sa.String(160), nullable=False, unique=True), sa.Column("business_unit_id", sa.Integer(), sa.ForeignKey("business_units.id"), nullable=False)); op.create_index("ix_applications_business_unit_id", "applications", ["business_unit_id"])
    if not _has_table("users"):
        op.create_table("users", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("username", sa.String(80), nullable=False, unique=True), sa.Column("password_hash", sa.String(255), nullable=False), sa.Column("role_id", sa.Integer(), sa.ForeignKey("roles.id"), nullable=False), sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true())); op.create_index("ix_users_username", "users", ["username"])
    if not _has_table("controls"):
        op.create_table("controls", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("name", sa.String(120), nullable=False, unique=True), sa.Column("category", sa.String(80), nullable=False), sa.Column("implementation_cost", sa.Float(), nullable=False), sa.Column("baseline_effectiveness", sa.Float(), nullable=False))
    if not _has_table("vulnerabilities"):
        op.create_table("vulnerabilities", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("asset_id", sa.Integer(), sa.ForeignKey("assets.id"), nullable=False), sa.Column("cve_id", sa.String(30), nullable=False), sa.Column("cvss", sa.Float(), nullable=False), sa.Column("exploitability", sa.Float(), nullable=False), sa.Column("status", sa.String(30), nullable=False), sa.Column("source_id", sa.String(80), nullable=False), sa.Column("source_event_id", sa.String(100), nullable=False), sa.UniqueConstraint("source_id", "source_event_id", name="uq_source_event")); op.create_index("ix_vulnerabilities_asset_id", "vulnerabilities", ["asset_id"]); op.create_index("ix_vulnerabilities_cve_id", "vulnerabilities", ["cve_id"])
    if not _has_table("incidents"):
        op.create_table("incidents", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("asset_id", sa.Integer(), sa.ForeignKey("assets.id"), nullable=False), sa.Column("severity", sa.String(20), nullable=False), sa.Column("financial_loss", sa.Float(), nullable=False), sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False)); op.create_index("ix_incidents_asset_id", "incidents", ["asset_id"])
    if not _has_table("threat_scenarios"):
        op.create_table("threat_scenarios", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("name", sa.String(160), nullable=False, unique=True), sa.Column("threat_type", sa.String(80), nullable=False), sa.Column("activity", sa.Float(), nullable=False))
    if not _has_table("investment_options"):
        op.create_table("investment_options", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("code", sa.String(60), nullable=False, unique=True), sa.Column("name", sa.String(160), nullable=False), sa.Column("cost", sa.Float(), nullable=False), sa.Column("risk_reduction", sa.Float(), nullable=False))
    if not _has_table("framework_mappings"):
        op.create_table("framework_mappings", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("framework", sa.String(80), nullable=False), sa.Column("control_reference", sa.String(80), nullable=False), sa.Column("control_id", sa.Integer(), sa.ForeignKey("controls.id"))); op.create_index("ix_framework_mappings_framework", "framework_mappings", ["framework"])
    if not _has_table("audit_events"):
        op.create_table("audit_events", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("event_hash", sa.String(64), nullable=False, unique=True), sa.Column("previous_hash", sa.String(64), nullable=False), sa.Column("payload", sa.Text(), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))
    if not _has_table("ingestion_events"):
        op.create_table("ingestion_events", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("source_id", sa.String(80), nullable=False), sa.Column("source_type", sa.String(40), nullable=False), sa.Column("source_event_id", sa.String(100), nullable=False), sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False), sa.Column("received_at", sa.DateTime(timezone=True), nullable=False), sa.Column("payload_hash", sa.String(64), nullable=False), sa.UniqueConstraint("source_id", "source_event_id", name="uq_ingestion_source_event")); op.create_index("ix_ingestion_events_source_id", "ingestion_events", ["source_id"]); op.create_index("ix_ingestion_events_source_type", "ingestion_events", ["source_type"])
    if not _has_table("risk_assessments"):
        op.create_table("risk_assessments", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("target_key", sa.String(100), nullable=False, unique=True), sa.Column("scope", sa.String(30), nullable=False), sa.Column("business_unit_id", sa.Integer(), sa.ForeignKey("business_units.id")), sa.Column("asset_id", sa.Integer(), sa.ForeignKey("assets.id")), sa.Column("application_id", sa.Integer(), sa.ForeignKey("applications.id")), sa.Column("risk_score", sa.Float(), nullable=False), sa.Column("likelihood", sa.Float(), nullable=False), sa.Column("financial_impact", sa.Float(), nullable=False), sa.Column("expected_annual_loss", sa.Float(), nullable=False), sa.Column("var_95", sa.Float(), nullable=False), sa.Column("model_version", sa.String(20), nullable=False), sa.Column("major_risk_drivers", sa.JSON(), nullable=False), sa.Column("assumptions", sa.JSON(), nullable=False), sa.Column("confidence", sa.Float(), nullable=False), sa.Column("data_freshness", sa.DateTime(timezone=True), nullable=False), sa.Column("calculated_at", sa.DateTime(timezone=True), nullable=False)); op.create_index("ix_risk_assessments_scope", "risk_assessments", ["scope"]); op.create_index("ix_risk_assessments_asset_id", "risk_assessments", ["asset_id"]); op.create_index("ix_risk_assessments_business_unit_id", "risk_assessments", ["business_unit_id"]); op.create_index("ix_risk_assessments_application_id", "risk_assessments", ["application_id"])
    else:
        columns = {column["name"] for column in sa.inspect(op.get_bind()).get_columns("risk_assessments")}
        indexes = {index["name"] for index in sa.inspect(op.get_bind()).get_indexes("risk_assessments")}
        additions = [("target_key", sa.String(100)), ("scope", sa.String(30)), ("business_unit_id", sa.Integer()), ("application_id", sa.Integer()), ("risk_score", sa.Float()), ("financial_impact", sa.Float()), ("major_risk_drivers", sa.JSON()), ("assumptions", sa.JSON()), ("confidence", sa.Float()), ("data_freshness", sa.DateTime(timezone=True)), ("calculated_at", sa.DateTime(timezone=True))]
        with op.batch_alter_table("risk_assessments") as batch:
            for name, column_type in additions:
                if name not in columns:
                    batch.add_column(sa.Column(name, column_type, nullable=True))
            if "uq_risk_assessments_target_key" not in indexes:
                batch.create_index("uq_risk_assessments_target_key", ["target_key"], unique=True)
            if "ix_risk_assessments_scope" not in indexes:
                batch.create_index("ix_risk_assessments_scope", ["scope"])
        # Existing, empty legacy tables are supported; new assessments always populate every field.

def downgrade() -> None:
    # This initial migration deliberately preserves operational data on downgrade.
    pass
