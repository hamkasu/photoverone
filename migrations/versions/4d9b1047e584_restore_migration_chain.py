"""Restore migration chain (no-op)

Revision ID: 4d9b1047e584
Revises: 778d12c5b758
Create Date: 2025-09-23 05:12:32.032973

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4d9b1047e584'
down_revision = '778d12c5b758'
branch_labels = None
depends_on = None


def upgrade():
    # No-op migration to restore the chain
    pass


def downgrade():
    # No-op migration to restore the chain
    pass