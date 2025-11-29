"""Add composite indexes for performance

Revision ID: 008
Revises: 007
Create Date: 2025-11-28 04:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '008'
down_revision: Union[str, None] = '007'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Users - frequent lookups by tenant + email, tenant + role
    op.create_index(
        'ix_users_tenant_email',
        'users',
        ['tenant_id', 'email'],
        unique=False
    )
    op.create_index(
        'ix_users_tenant_role',
        'users',
        ['tenant_id', 'role'],
        unique=False
    )
    op.create_index(
        'ix_users_tenant_active',
        'users',
        ['tenant_id', 'is_active'],
        unique=False
    )

    # Onboarding Assignments - frequent queries by status, user, flow
    op.create_index(
        'ix_assignments_tenant_status',
        'onboarding_assignments',
        ['tenant_id', 'status'],
        unique=False
    )
    op.create_index(
        'ix_assignments_tenant_user',
        'onboarding_assignments',
        ['tenant_id', 'user_id'],
        unique=False
    )
    op.create_index(
        'ix_assignments_tenant_flow',
        'onboarding_assignments',
        ['tenant_id', 'flow_id'],
        unique=False
    )
    op.create_index(
        'ix_assignments_user_status',
        'onboarding_assignments',
        ['user_id', 'status'],
        unique=False
    )

    # Onboarding Flows - active flows per tenant
    op.create_index(
        'ix_flows_tenant_active',
        'onboarding_flows',
        ['tenant_id', 'is_active'],
        unique=False
    )

    # Module Progress - lookups by assignment
    op.create_index(
        'ix_progress_assignment_module',
        'module_progress',
        ['assignment_id', 'module_id'],
        unique=True
    )
    op.create_index(
        'ix_progress_assignment_completed',
        'module_progress',
        ['assignment_id', 'is_completed'],
        unique=False
    )

    # Content Blocks - searches by tenant + type
    op.create_index(
        'ix_content_tenant_type',
        'content_blocks',
        ['tenant_id', 'block_type'],
        unique=False
    )
    op.create_index(
        'ix_content_tenant_active',
        'content_blocks',
        ['tenant_id', 'is_active'],
        unique=False
    )

    # Email Logs - queries by type and status
    op.create_index(
        'ix_email_logs_tenant_type_sent',
        'email_logs',
        ['tenant_id', 'email_type', 'is_sent'],
        unique=False
    )


def downgrade() -> None:
    # Drop all composite indexes
    op.drop_index('ix_email_logs_tenant_type_sent', table_name='email_logs')
    op.drop_index('ix_content_tenant_active', table_name='content_blocks')
    op.drop_index('ix_content_tenant_type', table_name='content_blocks')
    op.drop_index('ix_progress_assignment_completed', table_name='module_progress')
    op.drop_index('ix_progress_assignment_module', table_name='module_progress')
    op.drop_index('ix_flows_tenant_active', table_name='onboarding_flows')
    op.drop_index('ix_assignments_user_status', table_name='onboarding_assignments')
    op.drop_index('ix_assignments_tenant_flow', table_name='onboarding_assignments')
    op.drop_index('ix_assignments_tenant_user', table_name='onboarding_assignments')
    op.drop_index('ix_assignments_tenant_status', table_name='onboarding_assignments')
    op.drop_index('ix_users_tenant_active', table_name='users')
    op.drop_index('ix_users_tenant_role', table_name='users')
    op.drop_index('ix_users_tenant_email', table_name='users')
