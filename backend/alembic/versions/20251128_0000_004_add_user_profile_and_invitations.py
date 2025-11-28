"""Add user profile fields and user_invitations table

Revision ID: 004_user_profile_invitations
Revises: 003_user_tenant_fk
Create Date: 2025-11-28 00:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '004_user_profile_invitations'
down_revision: Union[str, None] = '003_user_tenant_fk'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add new profile columns to users table
    op.add_column('users', sa.Column('avatar_url', sa.String(500), nullable=True, comment='URL to user avatar image'))
    op.add_column('users', sa.Column('phone', sa.String(50), nullable=True, comment='User phone number'))
    op.add_column('users', sa.Column('job_title', sa.String(100), nullable=True, comment='User job title'))
    op.add_column('users', sa.Column('department', sa.String(100), nullable=True, comment='User department'))

    # Create user_invitations table
    op.create_table(
        'user_invitations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(255), nullable=False, comment='Email to send invitation to'),
        sa.Column('token', sa.String(100), nullable=False, comment='Unique invitation token'),
        sa.Column('role', sa.String(50), nullable=False, comment='Role to assign when accepted'),
        sa.Column('tenant_id', sa.Integer(), nullable=False, comment='Foreign key to tenant'),
        sa.Column('invited_by', sa.Integer(), nullable=True, comment='User who sent the invitation'),
        sa.Column('is_accepted', sa.Boolean(), nullable=False, default=False, comment='Whether invitation was accepted'),
        sa.Column('accepted_at', sa.DateTime(), nullable=True, comment='When invitation was accepted'),
        sa.Column('expires_at', sa.DateTime(), nullable=False, comment='When invitation expires'),
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

    # Remove profile columns from users table
    op.drop_column('users', 'department')
    op.drop_column('users', 'job_title')
    op.drop_column('users', 'phone')
    op.drop_column('users', 'avatar_url')
