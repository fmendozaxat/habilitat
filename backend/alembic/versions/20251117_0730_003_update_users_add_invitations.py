"""update users and add invitations table

Revision ID: 003_users_update
Revises: 002_users_auth
Create Date: 2025-11-17 07:30:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '003_users_update'
down_revision: Union[str, None] = '002_users_auth'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add new profile fields to users table
    op.add_column('users', sa.Column('avatar_url', sa.String(length=500), nullable=True, comment='User avatar URL'))
    op.add_column('users', sa.Column('phone', sa.String(length=50), nullable=True, comment='User phone number'))
    op.add_column('users', sa.Column('job_title', sa.String(length=100), nullable=True, comment='User job title'))
    op.add_column('users', sa.Column('department', sa.String(length=100), nullable=True, comment='User department'))

    # Create user_invitations table
    op.create_table(
        'user_invitations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tenant_id', sa.Integer(), nullable=False, comment='Foreign key to tenant'),
        sa.Column('email', sa.String(length=255), nullable=False, comment='Email address of invited user'),
        sa.Column('token', sa.String(length=100), nullable=False, comment='Unique invitation token'),
        sa.Column('role', sa.String(length=50), nullable=False, comment='Role to be assigned when accepted'),
        sa.Column('invited_by', sa.Integer(), nullable=True, comment='User ID who created the invitation'),
        sa.Column('is_accepted', sa.Boolean(), nullable=False, comment='Whether invitation has been accepted'),
        sa.Column('accepted_at', sa.DateTime(), nullable=True, comment='When invitation was accepted'),
        sa.Column('expires_at', sa.DateTime(), nullable=False, comment='Invitation expiration time'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['invited_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_invitations_id'), 'user_invitations', ['id'], unique=False)
    op.create_index(op.f('ix_user_invitations_email'), 'user_invitations', ['email'], unique=False)
    op.create_index(op.f('ix_user_invitations_token'), 'user_invitations', ['token'], unique=True)
    op.create_index(op.f('ix_user_invitations_tenant_id'), 'user_invitations', ['tenant_id'], unique=False)


def downgrade() -> None:
    # Drop user_invitations table
    op.drop_index(op.f('ix_user_invitations_tenant_id'), table_name='user_invitations')
    op.drop_index(op.f('ix_user_invitations_token'), table_name='user_invitations')
    op.drop_index(op.f('ix_user_invitations_email'), table_name='user_invitations')
    op.drop_index(op.f('ix_user_invitations_id'), table_name='user_invitations')
    op.drop_table('user_invitations')

    # Remove new columns from users table
    op.drop_column('users', 'department')
    op.drop_column('users', 'job_title')
    op.drop_column('users', 'phone')
    op.drop_column('users', 'avatar_url')
