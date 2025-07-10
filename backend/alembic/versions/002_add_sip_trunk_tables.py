"""Add SIP trunk tables

Revision ID: 002
Revises: 001
Create Date: 2025-01-07 17:28:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create SIP trunks table
    op.create_table('sip_trunks',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('provider', sa.Enum('TWILIO', 'TELNYX', 'BANDWIDTH', 'VONAGE', 'CUSTOM', name='siptrunktprovider'), nullable=False),
        sa.Column('status', sa.Enum('ACTIVE', 'INACTIVE', 'SUSPENDED', 'MAINTENANCE', 'ERROR', name='siptrunkstatus'), nullable=False),
        sa.Column('sip_domain', sa.String(length=255), nullable=False),
        sa.Column('sip_username', sa.String(length=100), nullable=False),
        sa.Column('sip_password', sa.String(length=255), nullable=False),
        sa.Column('sip_proxy', sa.String(length=255), nullable=True),
        sa.Column('sip_port', sa.Integer(), nullable=False),
        sa.Column('auth_username', sa.String(length=100), nullable=True),
        sa.Column('auth_password', sa.String(length=255), nullable=True),
        sa.Column('inbound_routing', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('outbound_routing', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('call_direction', sa.Enum('INBOUND', 'OUTBOUND', 'BIDIRECTIONAL', name='calldirection'), nullable=False),
        sa.Column('max_concurrent_calls', sa.Integer(), nullable=False),
        sa.Column('current_active_calls', sa.Integer(), nullable=False),
        sa.Column('codec_preferences', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('dtmf_mode', sa.String(length=20), nullable=False),
        sa.Column('last_health_check', sa.DateTime(timezone=True), nullable=True),
        sa.Column('health_status', sa.String(length=20), nullable=False),
        sa.Column('latency_ms', sa.Float(), nullable=True),
        sa.Column('packet_loss_percent', sa.Float(), nullable=True),
        sa.Column('cost_per_minute', sa.Float(), nullable=False),
        sa.Column('monthly_cost', sa.Float(), nullable=False),
        sa.Column('allowed_ips', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('encryption_enabled', sa.Boolean(), nullable=False),
        sa.Column('failover_trunk_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('priority', sa.Integer(), nullable=False),
        sa.Column('custom_headers', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('advanced_config', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['failover_trunk_id'], ['sip_trunks.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_sip_trunks_id'), 'sip_trunks', ['id'], unique=False)
    op.create_index(op.f('ix_sip_trunks_user_id'), 'sip_trunks', ['user_id'], unique=False)

    # Create call logs table
    op.create_table('call_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('sip_trunk_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('call_id', sa.String(length=100), nullable=False),
        sa.Column('direction', sa.Enum('INBOUND', 'OUTBOUND', 'BIDIRECTIONAL', name='calldirection'), nullable=False),
        sa.Column('from_number', sa.String(length=20), nullable=False),
        sa.Column('to_number', sa.String(length=20), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('answered_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('ended_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('duration_seconds', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('hangup_cause', sa.String(length=50), nullable=True),
        sa.Column('quality_score', sa.Float(), nullable=True),
        sa.Column('codec_used', sa.String(length=20), nullable=True),
        sa.Column('sip_call_id', sa.String(length=255), nullable=True),
        sa.Column('remote_ip', sa.String(length=45), nullable=True),
        sa.Column('cost', sa.Float(), nullable=False),
        sa.Column('credits_used', sa.Integer(), nullable=False),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ),
        sa.ForeignKeyConstraint(['sip_trunk_id'], ['sip_trunks.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('call_id')
    )
    op.create_index(op.f('ix_call_logs_call_id'), 'call_logs', ['call_id'], unique=False)
    op.create_index(op.f('ix_call_logs_conversation_id'), 'call_logs', ['conversation_id'], unique=False)
    op.create_index(op.f('ix_call_logs_id'), 'call_logs', ['id'], unique=False)
    op.create_index(op.f('ix_call_logs_sip_trunk_id'), 'call_logs', ['sip_trunk_id'], unique=False)
    op.create_index(op.f('ix_call_logs_user_id'), 'call_logs', ['user_id'], unique=False)


def downgrade() -> None:
    # Drop call logs table
    op.drop_index(op.f('ix_call_logs_user_id'), table_name='call_logs')
    op.drop_index(op.f('ix_call_logs_sip_trunk_id'), table_name='call_logs')
    op.drop_index(op.f('ix_call_logs_id'), table_name='call_logs')
    op.drop_index(op.f('ix_call_logs_conversation_id'), table_name='call_logs')
    op.drop_index(op.f('ix_call_logs_call_id'), table_name='call_logs')
    op.drop_table('call_logs')
    
    # Drop SIP trunks table
    op.drop_index(op.f('ix_sip_trunks_user_id'), table_name='sip_trunks')
    op.drop_index(op.f('ix_sip_trunks_id'), table_name='sip_trunks')
    op.drop_table('sip_trunks')
    
    # Drop enums
    op.execute('DROP TYPE IF EXISTS calldirection')
    op.execute('DROP TYPE IF EXISTS siptrunkstatus')
    op.execute('DROP TYPE IF EXISTS siptrunktprovider')