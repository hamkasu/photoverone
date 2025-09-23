"""Safe add photo metadata columns with conditional logic

Revision ID: 4d9b1047e585
Revises: 778d12c5b758
Create Date: 2025-09-23 05:20:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision = '4d9b1047e585'
down_revision = '4d9b1047e584'
branch_labels = None
depends_on = None


def column_exists(table_name, column_name):
    """Check if a column exists in the table"""
    conn = op.get_bind()
    inspector = inspect(conn)
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns


def upgrade():
    # Define all columns to add
    columns_to_add = [
        ('camera_make', sa.String(100)),
        ('camera_model', sa.String(100)),
        ('iso', sa.Integer()),
        ('aperture', sa.Float()),
        ('shutter_speed', sa.String(50)),
        ('focal_length', sa.Float()),
        ('flash_used', sa.Boolean()),
        ('gps_latitude', sa.Float()),
        ('gps_longitude', sa.Float()),
        ('gps_altitude', sa.Float()),
        ('location_name', sa.String(255)),
        ('orientation', sa.Integer()),
        ('color_space', sa.String(50)),
        ('enhancement_settings', sa.Text()),
        ('description', sa.Text()),
        ('tags', sa.String(500)),
        ('event_name', sa.String(255)),
        ('estimated_year', sa.Integer()),
        ('edited_path', sa.String(500)),
    ]
    
    # Add each column only if it doesn't exist
    for column_name, column_type in columns_to_add:
        if not column_exists('photo', column_name):
            op.add_column('photo', sa.Column(column_name, column_type, nullable=True))


def downgrade():
    # Only drop columns that actually exist
    columns_to_drop = [
        'edited_path',
        'estimated_year',
        'event_name',
        'tags',
        'description',
        'enhancement_settings',
        'color_space',
        'orientation',
        'location_name',
        'gps_altitude',
        'gps_longitude',
        'gps_latitude',
        'flash_used',
        'focal_length',
        'shutter_speed',
        'aperture',
        'iso',
        'camera_model',
        'camera_make'
    ]
    
    for column_name in columns_to_drop:
        if column_exists('photo', column_name):
            op.drop_column('photo', column_name)