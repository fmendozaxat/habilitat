"""create notifications tables

Revision ID: 006_notifications
Revises: 005_content
Create Date: 2025-11-17 09:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '006_notifications'
down_revision: Union[str, None] = '005_content'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create email_logs table
    op.create_table(
        'email_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tenant_id', sa.Integer(), nullable=False, comment='Foreign key to tenant'),
        sa.Column('to_email', sa.String(length=255), nullable=False, comment='Email del destinatario'),
        sa.Column('to_name', sa.String(length=200), nullable=True, comment='Nombre del destinatario'),
        sa.Column('subject', sa.String(length=500), nullable=False, comment='Asunto del email'),
        sa.Column('email_type', sa.String(length=50), nullable=False, comment='Tipo de email (welcome, invitation, etc)'),
        sa.Column('template_name', sa.String(length=100), nullable=True, comment='Nombre del template utilizado'),
        sa.Column('template_data', sa.JSON(), nullable=True, comment='Variables pasadas al template'),
        sa.Column('is_sent', sa.Boolean(), nullable=False, comment='Si el email fue enviado exitosamente'),
        sa.Column('sent_at', sa.DateTime(), nullable=True, comment='Timestamp del envío'),
        sa.Column('error_message', sa.Text(), nullable=True, comment='Mensaje de error si falló'),
        sa.Column('external_id', sa.String(length=200), nullable=True, comment='ID externo del proveedor (SendGrid, etc)'),
        sa.Column('user_id', sa.Integer(), nullable=True, comment='ID del usuario relacionado (opcional)'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_email_logs_id'), 'email_logs', ['id'], unique=False)
    op.create_index(op.f('ix_email_logs_tenant_id'), 'email_logs', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_email_logs_to_email'), 'email_logs', ['to_email'], unique=False)
    op.create_index(op.f('ix_email_logs_email_type'), 'email_logs', ['email_type'], unique=False)


def downgrade() -> None:
    # Drop email_logs table
    op.drop_index(op.f('ix_email_logs_email_type'), table_name='email_logs')
    op.drop_index(op.f('ix_email_logs_to_email'), table_name='email_logs')
    op.drop_index(op.f('ix_email_logs_tenant_id'), table_name='email_logs')
    op.drop_index(op.f('ix_email_logs_id'), table_name='email_logs')
    op.drop_table('email_logs')
