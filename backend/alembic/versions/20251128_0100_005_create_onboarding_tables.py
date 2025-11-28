"""Create onboarding tables

Revision ID: 005_onboarding
Revises: 004_user_profile_invitations
Create Date: 2025-11-28 01:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '005_onboarding'
down_revision: Union[str, None] = '004_user_profile_invitations'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create onboarding_flows table
    op.create_table(
        'onboarding_flows',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tenant_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('is_template', sa.Boolean(), nullable=False, default=False),
        sa.Column('display_order', sa.Integer(), nullable=False, default=0),
        sa.Column('settings', sa.JSON(), nullable=False, default={}),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_onboarding_flows_id'), 'onboarding_flows', ['id'], unique=False)
    op.create_index(op.f('ix_onboarding_flows_tenant_id'), 'onboarding_flows', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_onboarding_flows_deleted_at'), 'onboarding_flows', ['deleted_at'], unique=False)

    # Create onboarding_modules table
    op.create_table(
        'onboarding_modules',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('flow_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('content_type', sa.String(50), nullable=False),
        sa.Column('content_text', sa.Text(), nullable=True),
        sa.Column('content_url', sa.String(500), nullable=True),
        sa.Column('order', sa.Integer(), nullable=False, default=0),
        sa.Column('is_required', sa.Boolean(), nullable=False, default=True),
        sa.Column('requires_completion_confirmation', sa.Boolean(), nullable=False, default=False),
        sa.Column('quiz_data', sa.JSON(), nullable=True),
        sa.Column('estimated_minutes', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['flow_id'], ['onboarding_flows.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_onboarding_modules_id'), 'onboarding_modules', ['id'], unique=False)
    op.create_index(op.f('ix_onboarding_modules_flow_id'), 'onboarding_modules', ['flow_id'], unique=False)

    # Create onboarding_assignments table
    op.create_table(
        'onboarding_assignments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tenant_id', sa.Integer(), nullable=False),
        sa.Column('flow_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(50), nullable=False, default='not_started'),
        sa.Column('assigned_at', sa.DateTime(), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('due_date', sa.DateTime(), nullable=True),
        sa.Column('completion_percentage', sa.Integer(), nullable=False, default=0),
        sa.Column('assigned_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['flow_id'], ['onboarding_flows.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['assigned_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_onboarding_assignments_id'), 'onboarding_assignments', ['id'], unique=False)
    op.create_index(op.f('ix_onboarding_assignments_tenant_id'), 'onboarding_assignments', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_onboarding_assignments_flow_id'), 'onboarding_assignments', ['flow_id'], unique=False)
    op.create_index(op.f('ix_onboarding_assignments_user_id'), 'onboarding_assignments', ['user_id'], unique=False)

    # Create module_progress table
    op.create_table(
        'module_progress',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('assignment_id', sa.Integer(), nullable=False),
        sa.Column('module_id', sa.Integer(), nullable=False),
        sa.Column('is_completed', sa.Boolean(), nullable=False, default=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('time_spent_minutes', sa.Integer(), nullable=False, default=0),
        sa.Column('quiz_score', sa.Integer(), nullable=True),
        sa.Column('quiz_passed', sa.Boolean(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['assignment_id'], ['onboarding_assignments.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['module_id'], ['onboarding_modules.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_module_progress_id'), 'module_progress', ['id'], unique=False)
    op.create_index(op.f('ix_module_progress_assignment_id'), 'module_progress', ['assignment_id'], unique=False)
    op.create_index(op.f('ix_module_progress_module_id'), 'module_progress', ['module_id'], unique=False)


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_index(op.f('ix_module_progress_module_id'), table_name='module_progress')
    op.drop_index(op.f('ix_module_progress_assignment_id'), table_name='module_progress')
    op.drop_index(op.f('ix_module_progress_id'), table_name='module_progress')
    op.drop_table('module_progress')

    op.drop_index(op.f('ix_onboarding_assignments_user_id'), table_name='onboarding_assignments')
    op.drop_index(op.f('ix_onboarding_assignments_flow_id'), table_name='onboarding_assignments')
    op.drop_index(op.f('ix_onboarding_assignments_tenant_id'), table_name='onboarding_assignments')
    op.drop_index(op.f('ix_onboarding_assignments_id'), table_name='onboarding_assignments')
    op.drop_table('onboarding_assignments')

    op.drop_index(op.f('ix_onboarding_modules_flow_id'), table_name='onboarding_modules')
    op.drop_index(op.f('ix_onboarding_modules_id'), table_name='onboarding_modules')
    op.drop_table('onboarding_modules')

    op.drop_index(op.f('ix_onboarding_flows_deleted_at'), table_name='onboarding_flows')
    op.drop_index(op.f('ix_onboarding_flows_tenant_id'), table_name='onboarding_flows')
    op.drop_index(op.f('ix_onboarding_flows_id'), table_name='onboarding_flows')
    op.drop_table('onboarding_flows')
