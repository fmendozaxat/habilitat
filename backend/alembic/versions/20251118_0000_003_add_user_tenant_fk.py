"""Add explicit foreign key constraint to users.tenant_id

Revision ID: 003_user_tenant_fk
Revises: 002_users_auth
Create Date: 2025-11-18 00:00:00

Note: This migration is now a no-op because the FK was already created in 002.
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
    # FK already exists from migration 002, nothing to do
    pass


def downgrade() -> None:
    # Nothing to undo
    pass
