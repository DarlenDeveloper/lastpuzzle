"""Add account_id fields to all tables

Revision ID: 003_add_account_id_fields
Revises: 002_add_sip_trunk_tables
Create Date: 2025-01-07 17:42:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import secrets
import string

# revision identifiers, used by Alembic.
revision = '003_add_account_id_fields'
down_revision = '002_add_sip_trunk_tables'
branch_labels = None
depends_on = None


def generate_account_id() -> str:
    """Generate a unique account ID"""
    chars = string.ascii_uppercase + string.digits
    random_part = ''.join(secrets.choice(chars) for _ in range(12))
    return f"ACC_{random_part}"


def upgrade() -> None:
    """Add account_id fields to all tables"""
    
    # Add account_id to users table
    op.add_column('users', sa.Column('account_id', sa.String(32), nullable=True))
    
    # Create unique index on account_id
    op.create_index('ix_users_account_id', 'users', ['account_id'])
    op.create_unique_constraint('uq_users_account_id', 'users', ['account_id'])
    
    # Update existing users with account IDs
    connection = op.get_bind()
    result = connection.execute(sa.text("SELECT id FROM users"))
    users = result.fetchall()
    
    for user in users:
        account_id = generate_account_id()
        connection.execute(
            sa.text("UPDATE users SET account_id = :account_id WHERE id = :user_id"),
            {"account_id": account_id, "user_id": user[0]}
        )
    
    # Make account_id non-nullable after populating
    op.alter_column('users', 'account_id', nullable=False)
    
    # Add account_id to agents table
    op.add_column('agents', sa.Column('account_id', sa.String(32), nullable=True))
    op.create_index('ix_agents_account_id', 'agents', ['account_id'])
    
    # Update agents with their user's account_id
    connection.execute(sa.text("""
        UPDATE agents 
        SET account_id = users.account_id 
        FROM users 
        WHERE agents.user_id = users.id
    """))
    
    op.alter_column('agents', 'account_id', nullable=False)
    
    # Add account_id to conversations table
    op.add_column('conversations', sa.Column('account_id', sa.String(32), nullable=True))
    op.create_index('ix_conversations_account_id', 'conversations', ['account_id'])
    
    # Update conversations with their user's account_id
    connection.execute(sa.text("""
        UPDATE conversations 
        SET account_id = users.account_id 
        FROM users 
        WHERE conversations.user_id = users.id
    """))
    
    op.alter_column('conversations', 'account_id', nullable=False)
    
    # Add account_id to usage_logs table
    op.add_column('usage_logs', sa.Column('account_id', sa.String(32), nullable=True))
    op.create_index('ix_usage_logs_account_id', 'usage_logs', ['account_id'])
    
    # Update usage_logs with their user's account_id
    connection.execute(sa.text("""
        UPDATE usage_logs 
        SET account_id = users.account_id 
        FROM users 
        WHERE usage_logs.user_id = users.id
    """))
    
    op.alter_column('usage_logs', 'account_id', nullable=False)
    
    # Add account_id to credit_transactions table
    op.add_column('credit_transactions', sa.Column('account_id', sa.String(32), nullable=True))
    op.create_index('ix_credit_transactions_account_id', 'credit_transactions', ['account_id'])
    
    # Update credit_transactions with their user's account_id
    connection.execute(sa.text("""
        UPDATE credit_transactions 
        SET account_id = users.account_id 
        FROM users 
        WHERE credit_transactions.user_id = users.id
    """))
    
    op.alter_column('credit_transactions', 'account_id', nullable=False)
    
    # Add account_id to usage_summaries table
    op.add_column('usage_summaries', sa.Column('account_id', sa.String(32), nullable=True))
    op.create_index('ix_usage_summaries_account_id', 'usage_summaries', ['account_id'])
    
    # Update usage_summaries with their user's account_id
    connection.execute(sa.text("""
        UPDATE usage_summaries 
        SET account_id = users.account_id 
        FROM users 
        WHERE usage_summaries.user_id = users.id
    """))
    
    op.alter_column('usage_summaries', 'account_id', nullable=False)
    
    # Add account_id to user_subscriptions table
    op.add_column('user_subscriptions', sa.Column('account_id', sa.String(32), nullable=True))
    op.create_index('ix_user_subscriptions_account_id', 'user_subscriptions', ['account_id'])
    
    # Update user_subscriptions with their user's account_id
    connection.execute(sa.text("""
        UPDATE user_subscriptions 
        SET account_id = users.account_id 
        FROM users 
        WHERE user_subscriptions.user_id = users.id
    """))
    
    op.alter_column('user_subscriptions', 'account_id', nullable=False)
    
    # Add account_id to knowledge_bases table
    op.add_column('knowledge_bases', sa.Column('account_id', sa.String(32), nullable=True))
    op.create_index('ix_knowledge_bases_account_id', 'knowledge_bases', ['account_id'])
    
    # Update knowledge_bases with their user's account_id
    connection.execute(sa.text("""
        UPDATE knowledge_bases 
        SET account_id = users.account_id 
        FROM users 
        WHERE knowledge_bases.user_id = users.id
    """))
    
    op.alter_column('knowledge_bases', 'account_id', nullable=False)
    
    # Add account_id to documents table
    op.add_column('documents', sa.Column('account_id', sa.String(32), nullable=True))
    op.create_index('ix_documents_account_id', 'documents', ['account_id'])
    
    # Update documents with their user's account_id
    connection.execute(sa.text("""
        UPDATE documents 
        SET account_id = users.account_id 
        FROM users 
        WHERE documents.user_id = users.id
    """))
    
    op.alter_column('documents', 'account_id', nullable=False)
    
    # Add account_id to web_scrape_jobs table
    op.add_column('web_scrape_jobs', sa.Column('account_id', sa.String(32), nullable=True))
    op.create_index('ix_web_scrape_jobs_account_id', 'web_scrape_jobs', ['account_id'])
    
    # Update web_scrape_jobs with their user's account_id
    connection.execute(sa.text("""
        UPDATE web_scrape_jobs 
        SET account_id = users.account_id 
        FROM users 
        WHERE web_scrape_jobs.user_id = users.id
    """))
    
    op.alter_column('web_scrape_jobs', 'account_id', nullable=False)
    
    # Add account_id to query_logs table
    op.add_column('query_logs', sa.Column('account_id', sa.String(32), nullable=True))
    op.create_index('ix_query_logs_account_id', 'query_logs', ['account_id'])
    
    # Update query_logs with their user's account_id
    connection.execute(sa.text("""
        UPDATE query_logs 
        SET account_id = users.account_id 
        FROM users 
        WHERE query_logs.user_id = users.id
    """))
    
    op.alter_column('query_logs', 'account_id', nullable=False)
    
    # Add account_id to sip_trunks table
    op.add_column('sip_trunks', sa.Column('account_id', sa.String(32), nullable=True))
    op.create_index('ix_sip_trunks_account_id', 'sip_trunks', ['account_id'])
    
    # Update sip_trunks with their user's account_id
    connection.execute(sa.text("""
        UPDATE sip_trunks 
        SET account_id = users.account_id 
        FROM users 
        WHERE sip_trunks.user_id = users.id
    """))
    
    op.alter_column('sip_trunks', 'account_id', nullable=False)
    
    # Add account_id to call_logs table
    op.add_column('call_logs', sa.Column('account_id', sa.String(32), nullable=True))
    op.create_index('ix_call_logs_account_id', 'call_logs', ['account_id'])
    
    # Update call_logs with their user's account_id
    connection.execute(sa.text("""
        UPDATE call_logs 
        SET account_id = users.account_id 
        FROM users 
        WHERE call_logs.user_id = users.id
    """))
    
    op.alter_column('call_logs', 'account_id', nullable=False)


def downgrade() -> None:
    """Remove account_id fields from all tables"""
    
    # Remove account_id from all tables
    tables = [
        'call_logs', 'sip_trunks', 'query_logs', 'web_scrape_jobs', 
        'documents', 'knowledge_bases', 'user_subscriptions', 
        'usage_summaries', 'credit_transactions', 'usage_logs', 
        'conversations', 'agents', 'users'
    ]
    
    for table in tables:
        op.drop_index(f'ix_{table}_account_id', table_name=table)
        op.drop_column(table, 'account_id')
    
    # Remove unique constraint from users table
    op.drop_constraint('uq_users_account_id', 'users', type_='unique')