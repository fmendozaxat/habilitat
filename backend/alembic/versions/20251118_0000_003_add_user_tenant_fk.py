"""Add explicit foreign key constraint to users.tenant_id

Revision ID: 003_user_tenant_fk
Revises: 002_users_auth
Create Date: 2025-11-18 00:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '003_user_tenant_fk'
down_revision: Union[str, None] = '002_users_auth'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add explicit foreign key constraint to users.tenant_id."""
    # Create explicit foreign key constraint
    op.create_foreign_key(
        'users_tenant_id_fkey',
        'users',
        'tenants',
        ['tenant_id'],
        ['id'],
        ondelete='CASCADE'
    )


def downgrade() -> None:
    """Remove foreign key constraint from users.tenant_id."""
    op.drop_constraint('users_tenant_id_fkey', 'users', type_='foreignkey')
