"""Create email_logs table

Revision ID: 007
Revises: 006
Create Date: 2025-11-28 03:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '007'
down_revision: Union[str, None] = '006_content'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'email_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tenant_id', sa.Integer(), nullable=True),
        sa.Column('to_email', sa.String(255), nullable=False),
        sa.Column('to_name', sa.String(200), nullable=True),
        sa.Column('subject', sa.String(500), nullable=False),
        sa.Column('email_type', sa.String(50), nullable=False),
        sa.Column('template_name', sa.String(100), nullable=True),
        sa.Column('template_data', sa.JSON(), nullable=True),
        sa.Column('is_sent', sa.Boolean(), nullable=False, default=False),
        sa.Column('sent_at', sa.DateTime(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('external_id', sa.String(200), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes
    op.create_index('ix_email_logs_tenant_id', 'email_logs', ['tenant_id'])
    op.create_index('ix_email_logs_to_email', 'email_logs', ['to_email'])
    op.create_index('ix_email_logs_email_type', 'email_logs', ['email_type'])
    op.create_index('ix_email_logs_user_id', 'email_logs', ['user_id'])


def downgrade() -> None:
    op.drop_index('ix_email_logs_user_id', table_name='email_logs')
    op.drop_index('ix_email_logs_email_type', table_name='email_logs')
    op.drop_index('ix_email_logs_to_email', table_name='email_logs')
    op.drop_index('ix_email_logs_tenant_id', table_name='email_logs')
    op.drop_table('email_logs')
