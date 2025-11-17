"""create content tables

Revision ID: 005_content
Revises: 004_onboarding
Create Date: 2025-11-17 08:30:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '005_content'
down_revision: Union[str, None] = '004_onboarding'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create content_categories table
    op.create_table(
        'content_categories',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tenant_id', sa.Integer(), nullable=False, comment='Foreign key to tenant'),
        sa.Column('name', sa.String(length=100), nullable=False, comment='Category name'),
        sa.Column('slug', sa.String(length=100), nullable=False, comment='URL-friendly identifier'),
        sa.Column('description', sa.Text(), nullable=True, comment='Category description'),
        sa.Column('icon', sa.String(length=50), nullable=True, comment='Icon identifier (e.g., "folder", "book")'),
        sa.Column('color', sa.String(length=7), nullable=False, comment='Hex color code for UI'),
        sa.Column('is_active', sa.Boolean(), nullable=False, comment='Whether category is active'),
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
        sa.Column('tenant_id', sa.Integer(), nullable=False, comment='Foreign key to tenant'),
        sa.Column('title', sa.String(length=200), nullable=False, comment='Content title'),
        sa.Column('description', sa.Text(), nullable=True, comment='Content description/summary'),
        sa.Column('content_type', sa.String(length=50), nullable=False, comment='Type: text, image, video, pdf, link, quiz, task'),
        sa.Column('content_text', sa.Text(), nullable=True, comment='Main text content (for text type)'),
        sa.Column('content_url', sa.String(length=500), nullable=True, comment='URL for videos, PDFs, images, links'),
        sa.Column('content_metadata', sa.JSON(), nullable=True, comment='Additional metadata (JSON)'),
        sa.Column('category_id', sa.Integer(), nullable=True, comment='Foreign key to category'),
        sa.Column('tags', sa.JSON(), nullable=False, comment='Tags for filtering (JSON array)'),
        sa.Column('is_published', sa.Boolean(), nullable=False, comment='Whether content is published'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True, comment='Soft delete timestamp'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['category_id'], ['content_categories.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_content_blocks_id'), 'content_blocks', ['id'], unique=False)
    op.create_index(op.f('ix_content_blocks_tenant_id'), 'content_blocks', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_content_blocks_category_id'), 'content_blocks', ['category_id'], unique=False)
    op.create_index(op.f('ix_content_blocks_deleted_at'), 'content_blocks', ['deleted_at'], unique=False)

    # Add foreign key to onboarding_modules for content_id
    # Note: The column already exists from migration 004_onboarding, but FK wasn't created yet
    # Now we can create the FK since content_blocks table exists
    op.create_foreign_key(
        'fk_onboarding_modules_content_id',
        'onboarding_modules',
        'content_blocks',
        ['content_id'],
        ['id'],
        ondelete='SET NULL'
    )


def downgrade() -> None:
    # Remove FK from onboarding_modules
    op.drop_constraint('fk_onboarding_modules_content_id', 'onboarding_modules', type_='foreignkey')

    # Drop content tables in reverse order
    op.drop_index(op.f('ix_content_blocks_deleted_at'), table_name='content_blocks')
    op.drop_index(op.f('ix_content_blocks_category_id'), table_name='content_blocks')
    op.drop_index(op.f('ix_content_blocks_tenant_id'), table_name='content_blocks')
    op.drop_index(op.f('ix_content_blocks_id'), table_name='content_blocks')
    op.drop_table('content_blocks')

    op.drop_index(op.f('ix_content_categories_slug'), table_name='content_categories')
    op.drop_index(op.f('ix_content_categories_tenant_id'), table_name='content_categories')
    op.drop_index(op.f('ix_content_categories_id'), table_name='content_categories')
    op.drop_table('content_categories')
