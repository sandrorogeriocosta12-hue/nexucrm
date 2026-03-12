"""Add Company and User models for multi-tenant

Revision ID: 001
Revises: 
Create Date: 2026-02-13 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """Create companies and users tables"""
    
    # Create companies table
    op.create_table(
        'companies',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('owner_id', sa.Integer(), nullable=False),
        sa.Column('stripe_customer_id', sa.String(255), nullable=True),
        sa.Column('subscription_id', sa.String(255), nullable=True),
        sa.Column('plan', sa.String(50), server_default='starter'),
        sa.Column('status', sa.String(50), server_default='active'),
        sa.Column('is_active', sa.Boolean(), server_default=sa.true()),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_index('ix_companies_id', 'companies', ['id'], unique=False)
    
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('role', sa.String(50), server_default='member'),
        sa.Column('company_id', sa.String(36), nullable=True),
        sa.Column('is_verified', sa.Boolean(), server_default=sa.false()),
        sa.Column('is_active', sa.Boolean(), server_default=sa.true()),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )
    op.create_index('ix_users_email', 'users', ['email'], unique=False)
    op.create_index('ix_users_company_id', 'users', ['company_id'], unique=False)


def downgrade():
    """Drop tables"""
    op.drop_index('ix_users_company_id', table_name='users')
    op.drop_index('ix_users_email', table_name='users')
    op.drop_table('users')
    op.drop_index('ix_companies_id', table_name='companies')
    op.drop_table('companies')
