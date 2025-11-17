"""create tenants tables

Revision ID: 001_tenants
Revises:
Create Date: 2025-11-17 06:42:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001_tenants'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create tenants table
    op.create_table(
        'tenants',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False, comment='Organization name'),
        sa.Column('slug', sa.String(length=100), nullable=False, comment='URL-friendly identifier'),
        sa.Column('subdomain', sa.String(length=100), nullable=True, comment='Subdomain for tenant-specific access'),
        sa.Column('contact_email', sa.String(length=255), nullable=True),
        sa.Column('contact_phone', sa.String(length=50), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, comment='Whether the tenant is active'),
        sa.Column('plan', sa.String(length=50), nullable=False, comment='Subscription plan: free, starter, business, enterprise'),
        sa.Column('max_users', sa.Integer(), nullable=False, comment='Maximum number of users allowed'),
        sa.Column('max_storage_mb', sa.Integer(), nullable=False, comment='Maximum storage in MB (default: 1GB)'),
        sa.Column('settings', sa.JSON(), nullable=False, comment='Tenant-specific settings and configurations'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_tenants_id'), 'tenants', ['id'], unique=False)
    op.create_index(op.f('ix_tenants_slug'), 'tenants', ['slug'], unique=True)
    op.create_index(op.f('ix_tenants_subdomain'), 'tenants', ['subdomain'], unique=True)
    op.create_index(op.f('ix_tenants_deleted_at'), 'tenants', ['deleted_at'], unique=False)

    # Create tenant_branding table
    op.create_table(
        'tenant_branding',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tenant_id', sa.Integer(), nullable=False, comment='Foreign key to tenant'),
        sa.Column('logo_url', sa.String(length=500), nullable=True, comment='Main logo URL'),
        sa.Column('logo_dark_url', sa.String(length=500), nullable=True, comment='Logo for dark theme (optional)'),
        sa.Column('favicon_url', sa.String(length=500), nullable=True, comment='Favicon URL'),
        sa.Column('primary_color', sa.String(length=7), nullable=False, comment='Primary brand color (hex)'),
        sa.Column('secondary_color', sa.String(length=7), nullable=False, comment='Secondary brand color (hex)'),
        sa.Column('accent_color', sa.String(length=7), nullable=True, comment='Accent color (hex)'),
        sa.Column('background_color', sa.String(length=7), nullable=False, comment='Background color (hex)'),
        sa.Column('text_color', sa.String(length=7), nullable=False, comment='Text color (hex)'),
        sa.Column('hero_image_url', sa.String(length=500), nullable=True, comment='Hero section background image'),
        sa.Column('background_image_url', sa.String(length=500), nullable=True, comment='General background image'),
        sa.Column('font_family', sa.String(length=100), nullable=True, comment="Custom font family (e.g., 'Inter', 'Roboto')"),
        sa.Column('custom_css', sa.String(length=5000), nullable=True, comment='Custom CSS for advanced styling'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tenant_id')
    )
    op.create_index(op.f('ix_tenant_branding_id'), 'tenant_branding', ['id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_tenant_branding_id'), table_name='tenant_branding')
    op.drop_table('tenant_branding')

    op.drop_index(op.f('ix_tenants_deleted_at'), table_name='tenants')
    op.drop_index(op.f('ix_tenants_subdomain'), table_name='tenants')
    op.drop_index(op.f('ix_tenants_slug'), table_name='tenants')
    op.drop_index(op.f('ix_tenants_id'), table_name='tenants')
    op.drop_table('tenants')
