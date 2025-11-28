"""Create content tables

Revision ID: 006_content
Revises: 005_onboarding
Create Date: 2025-11-28 02:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '006_content'
down_revision: Union[str, None] = '005_onboarding'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create content_categories table
    op.create_table(
        'content_categories',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tenant_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('slug', sa.String(100), nullable=False),
        sa.Column('description', sa.String(500), nullable=True),
        sa.Column('color', sa.String(7), nullable=False, default='#6B7280'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_content_categories_id'), 'content_categories', ['id'], unique=False)
    op.create_index(op.f('ix_content_categories_tenant_id'), 'content_categories', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_content_categories_slug'), 'content_categories', ['slug'], unique=False)

    # Create content_blocks table
    op.create_table(
        'content_blocks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tenant_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('content_type', sa.String(50), nullable=False),
        sa.Column('content_text', sa.Text(), nullable=True),
        sa.Column('content_url', sa.String(500), nullable=True),
        sa.Column('content_metadata', sa.JSON(), nullable=True),
        sa.Column('category_id', sa.Integer(), nullable=True),
        sa.Column('tags', sa.JSON(), nullable=False, default=[]),
        sa.Column('is_published', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['category_id'], ['content_categories.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_content_blocks_id'), 'content_blocks', ['id'], unique=False)
    op.create_index(op.f('ix_content_blocks_tenant_id'), 'content_blocks', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_content_blocks_category_id'), 'content_blocks', ['category_id'], unique=False)
    op.create_index(op.f('ix_content_blocks_deleted_at'), 'content_blocks', ['deleted_at'], unique=False)


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_index(op.f('ix_content_blocks_deleted_at'), table_name='content_blocks')
    op.drop_index(op.f('ix_content_blocks_category_id'), table_name='content_blocks')
    op.drop_index(op.f('ix_content_blocks_tenant_id'), table_name='content_blocks')
    op.drop_index(op.f('ix_content_blocks_id'), table_name='content_blocks')
    op.drop_table('content_blocks')

    op.drop_index(op.f('ix_content_categories_slug'), table_name='content_categories')
    op.drop_index(op.f('ix_content_categories_tenant_id'), table_name='content_categories')
    op.drop_index(op.f('ix_content_categories_id'), table_name='content_categories')
    op.drop_table('content_categories')
