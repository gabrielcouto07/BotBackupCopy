"""Initial migration - Create all tables

Revision ID: 001
Create Date: 2024-01-01 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Enable UUID extension
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    
    # Create tenants table
    op.create_table(
        'tenants',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, 
                  server_default=sa.text('uuid_generate_v4()')),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('slug', sa.String(100), nullable=False, unique=True),
        sa.Column('subscription_tier', sa.String(50), nullable=False, server_default='free'),
        sa.Column('max_bots', sa.Integer, nullable=False, server_default='1'),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )
    
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('uuid_generate_v4()')),
        sa.Column('email', sa.String(255), nullable=False, unique=True),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('full_name', sa.String(255)),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('is_superuser', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )
    
    # Create tenant_users table
    op.create_table(
        'tenant_users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('uuid_generate_v4()')),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), 
                  sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('role', sa.String(50), nullable=False, server_default='member'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint('tenant_id', 'user_id', name='unique_tenant_user'),
    )
    
    # Create bot_configs table
    op.create_table(
        'bot_configs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('uuid_generate_v4()')),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(255), nullable=False, server_default='default'),
        sa.Column('source_urls', postgresql.JSONB, server_default='[]'),
        sa.Column('destination_config', postgresql.JSONB, server_default='{}'),
        sa.Column('interval_seconds', sa.Integer, nullable=False, server_default='60'),
        sa.Column('affiliate_config', postgresql.JSONB, server_default='{}'),
        sa.Column('filters', postgresql.JSONB, server_default='{}'),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint('tenant_id', 'name', name='unique_tenant_config_name'),
    )
    
    # Create bot_runs table
    op.create_table(
        'bot_runs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('uuid_generate_v4()')),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('config_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('bot_configs.id', ondelete='SET NULL')),
        sa.Column('status', sa.String(50), nullable=False, server_default='pending'),
        sa.Column('started_at', sa.TIMESTAMP(timezone=True)),
        sa.Column('finished_at', sa.TIMESTAMP(timezone=True)),
        sa.Column('items_processed', sa.Integer, server_default='0'),
        sa.Column('items_sent', sa.Integer, server_default='0'),
        sa.Column('error_message', sa.Text),
        sa.Column('metadata', postgresql.JSONB, server_default='{}'),
    )
    
    # Create bot_logs table
    op.create_table(
        'bot_logs',
        sa.Column('id', sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('run_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('bot_runs.id', ondelete='CASCADE')),
        sa.Column('level', sa.String(20), nullable=False, server_default='INFO'),
        sa.Column('message', sa.Text, nullable=False),
        sa.Column('context', postgresql.JSONB, server_default='{}'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )
    
    # Create tenant_secrets table
    op.create_table(
        'tenant_secrets',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('uuid_generate_v4()')),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('key_name', sa.String(100), nullable=False),
        sa.Column('encrypted_value', sa.Text, nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint('tenant_id', 'key_name', name='unique_tenant_secret'),
    )
    
    # Create bot_locks table
    op.create_table(
        'bot_locks',
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('worker_id', sa.String(255), nullable=False),
        sa.Column('acquired_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column('expires_at', sa.TIMESTAMP(timezone=True), nullable=False),
    )
    
    # Create audit_logs table
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('tenants.id', ondelete='CASCADE')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('users.id', ondelete='SET NULL')),
        sa.Column('action', sa.String(100), nullable=False),
        sa.Column('resource_type', sa.String(100)),
        sa.Column('resource_id', sa.String(255)),
        sa.Column('details', postgresql.JSONB, server_default='{}'),
        sa.Column('ip_address', sa.String(45)),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )
    
    # Create indexes
    op.create_index('idx_tenant_users_tenant', 'tenant_users', ['tenant_id'])
    op.create_index('idx_tenant_users_user', 'tenant_users', ['user_id'])
    op.create_index('idx_bot_configs_tenant', 'bot_configs', ['tenant_id'])
    op.create_index('idx_bot_runs_tenant', 'bot_runs', ['tenant_id'])
    op.create_index('idx_bot_runs_status', 'bot_runs', ['status'])
    op.create_index('idx_bot_logs_tenant', 'bot_logs', ['tenant_id'])
    op.create_index('idx_bot_logs_run', 'bot_logs', ['run_id'])
    op.create_index('idx_bot_logs_created', 'bot_logs', ['created_at'])
    op.create_index('idx_audit_logs_tenant', 'audit_logs', ['tenant_id'])
    op.create_index('idx_audit_logs_created', 'audit_logs', ['created_at'])


def downgrade() -> None:
    op.drop_table('audit_logs')
    op.drop_table('bot_locks')
    op.drop_table('tenant_secrets')
    op.drop_table('bot_logs')
    op.drop_table('bot_runs')
    op.drop_table('bot_configs')
    op.drop_table('tenant_users')
    op.drop_table('users')
    op.drop_table('tenants')
