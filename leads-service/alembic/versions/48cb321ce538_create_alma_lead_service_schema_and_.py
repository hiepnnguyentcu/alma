

"""Create alma_lead_service schema and leads table

Revision ID: d57706906f15
Revises: 
Create Date: 2025-10-03 21:59:37.065418

"""
from typing import Sequence, Union
import uuid

from alembic import op
import sqlalchemy as sa


revision: str = 'd57706906f15'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create schema
    op.execute("CREATE SCHEMA IF NOT EXISTS alma_lead_service")
    
    # Create leads table
    op.create_table('leads',
        sa.Column('id', sa.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('first_name', sa.String(length=100), nullable=False),
        sa.Column('last_name', sa.String(length=100), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('resume_path', sa.String(length=500), nullable=False),
        sa.Column('status', sa.Enum('PENDING', 'REACHED_OUT', name='leadstatus'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        schema='alma_lead_service'
    )
    op.create_index(op.f('ix_alma_lead_service_leads_id'), 'leads', ['id'], unique=False, schema='alma_lead_service')
    op.create_index(op.f('ix_alma_lead_service_leads_email'), 'leads', ['email'], unique=True, schema='alma_lead_service')


def downgrade() -> None:
    # Drop table
    op.drop_index(op.f('ix_alma_lead_service_leads_email'), table_name='leads', schema='alma_lead_service')
    op.drop_index(op.f('ix_alma_lead_service_leads_id'), table_name='leads', schema='alma_lead_service')
    op.drop_table('leads', schema='alma_lead_service')
    
    # Drop enum type
    op.execute("DROP TYPE IF EXISTS leadstatus")
    
    # Drop schema
    op.execute("DROP SCHEMA IF EXISTS alma_lead_service")