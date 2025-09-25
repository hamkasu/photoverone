"""Add is_active column back to user table

Revision ID: d5b4630ee3ad
Revises: 4d9b1047e585
Create Date: 2025-09-25 16:27:41.151767

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision = 'd5b4630ee3ad'
down_revision = '4d9b1047e585'
branch_labels = None
depends_on = None


def column_exists(table_name, column_name):
    """Check if a column exists in the table"""
    conn = op.get_bind()
    inspector = inspect(conn)
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns


def upgrade():
    # Add is_active column back to user table if it doesn't exist
    if not column_exists('user', 'is_active'):
        # Add column with default value True for existing users
        op.add_column('user', sa.Column('is_active', sa.Boolean(), nullable=True, default=True))
        
        # Update all existing records to have is_active = True
        conn = op.get_bind()
        conn.execute(sa.text("UPDATE \"user\" SET is_active = true WHERE is_active IS NULL"))
        
        # Make the column non-nullable after setting default values
        # Note: We keep it nullable=True to match the model definition


def downgrade():
    # Remove is_active column if it exists
    if column_exists('user', 'is_active'):
        op.drop_column('user', 'is_active')
