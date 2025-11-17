"""create onboarding tables

Revision ID: 004_onboarding
Revises: 003_users_update
Create Date: 2025-11-17 08:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '004_onboarding'
down_revision: Union[str, None] = '003_users_update'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create onboarding_flows table
    op.create_table(
        'onboarding_flows',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tenant_id', sa.Integer(), nullable=False, comment='Foreign key to tenant'),
        sa.Column('title', sa.String(length=200), nullable=False, comment='Flow title'),
        sa.Column('description', sa.Text(), nullable=True, comment='Flow description'),
        sa.Column('is_active', sa.Boolean(), nullable=False, comment='Whether flow is active'),
        sa.Column('is_template', sa.Boolean(), nullable=False, comment='Whether this is a predefined template'),
        sa.Column('display_order', sa.Integer(), nullable=False, comment='Display order for sorting'),
        sa.Column('settings', sa.JSON(), nullable=False, comment='Flow-specific settings'),
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
        sa.Column('flow_id', sa.Integer(), nullable=False, comment='Foreign key to flow'),
        sa.Column('title', sa.String(length=200), nullable=False, comment='Module title'),
        sa.Column('description', sa.Text(), nullable=True, comment='Module description'),
        sa.Column('content_type', sa.String(length=50), nullable=False, comment='Type of content: text, video, pdf, quiz, task, link'),
        sa.Column('content_id', sa.Integer(), nullable=True, comment='Link to ContentBlock (optional)'),
        sa.Column('content_text', sa.Text(), nullable=True, comment='Direct text content'),
        sa.Column('content_url', sa.String(length=500), nullable=True, comment='Video URL, PDF URL, etc.'),
        sa.Column('order', sa.Integer(), nullable=False, comment='Order within the flow'),
        sa.Column('is_required', sa.Boolean(), nullable=False, comment='Whether module is required'),
        sa.Column('requires_completion_confirmation', sa.Boolean(), nullable=False, comment='Whether explicit confirmation is needed'),
        sa.Column('quiz_data', sa.JSON(), nullable=True, comment='Quiz questions and answers'),
        sa.Column('estimated_minutes', sa.Integer(), nullable=True, comment='Estimated time to complete in minutes'),
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
        sa.Column('tenant_id', sa.Integer(), nullable=False, comment='Foreign key to tenant'),
        sa.Column('flow_id', sa.Integer(), nullable=False, comment='Foreign key to flow'),
        sa.Column('user_id', sa.Integer(), nullable=False, comment='Foreign key to user'),
        sa.Column('status', sa.String(length=50), nullable=False, comment='Status: not_started, in_progress, completed, expired'),
        sa.Column('assigned_at', sa.DateTime(), nullable=False, comment='When assigned'),
        sa.Column('started_at', sa.DateTime(), nullable=True, comment='When started'),
        sa.Column('completed_at', sa.DateTime(), nullable=True, comment='When completed'),
        sa.Column('due_date', sa.DateTime(), nullable=True, comment='Due date'),
        sa.Column('completion_percentage', sa.Integer(), nullable=False, comment='Completion percentage 0-100'),
        sa.Column('assigned_by', sa.Integer(), nullable=True, comment='User who assigned'),
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
        sa.Column('assignment_id', sa.Integer(), nullable=False, comment='Foreign key to assignment'),
        sa.Column('module_id', sa.Integer(), nullable=False, comment='Foreign key to module'),
        sa.Column('is_completed', sa.Boolean(), nullable=False, comment='Whether module is completed'),
        sa.Column('completed_at', sa.DateTime(), nullable=True, comment='When completed'),
        sa.Column('time_spent_minutes', sa.Integer(), nullable=False, comment='Time spent in minutes'),
        sa.Column('quiz_score', sa.Integer(), nullable=True, comment='Quiz score 0-100'),
        sa.Column('quiz_passed', sa.Boolean(), nullable=True, comment='Whether quiz was passed'),
        sa.Column('quiz_answers', sa.JSON(), nullable=True, comment="User's quiz answers"),
        sa.Column('notes', sa.Text(), nullable=True, comment='Employee notes'),
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
    # Drop tables in reverse order (child tables first)
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
