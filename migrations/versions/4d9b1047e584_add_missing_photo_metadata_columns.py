"""Add missing photo metadata columns

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
    # Add EXIF metadata columns
    op.add_column('photo', sa.Column('camera_make', sa.String(100), nullable=True))
    op.add_column('photo', sa.Column('camera_model', sa.String(100), nullable=True))
    op.add_column('photo', sa.Column('iso', sa.Integer(), nullable=True))
    op.add_column('photo', sa.Column('aperture', sa.Float(), nullable=True))
    op.add_column('photo', sa.Column('shutter_speed', sa.String(50), nullable=True))
    op.add_column('photo', sa.Column('focal_length', sa.Float(), nullable=True))
    op.add_column('photo', sa.Column('flash_used', sa.Boolean(), nullable=True))
    
    # Add GPS columns
    op.add_column('photo', sa.Column('gps_latitude', sa.Float(), nullable=True))
    op.add_column('photo', sa.Column('gps_longitude', sa.Float(), nullable=True))
    op.add_column('photo', sa.Column('gps_altitude', sa.Float(), nullable=True))
    op.add_column('photo', sa.Column('location_name', sa.String(255), nullable=True))
    
    # Add image properties
    op.add_column('photo', sa.Column('orientation', sa.Integer(), nullable=True))
    op.add_column('photo', sa.Column('color_space', sa.String(50), nullable=True))
    
    # Add enhancement settings
    op.add_column('photo', sa.Column('enhancement_settings', sa.Text(), nullable=True))
    
    # Add user metadata
    op.add_column('photo', sa.Column('description', sa.Text(), nullable=True))
    op.add_column('photo', sa.Column('tags', sa.String(500), nullable=True))
    op.add_column('photo', sa.Column('event_name', sa.String(255), nullable=True))
    op.add_column('photo', sa.Column('estimated_year', sa.Integer(), nullable=True))
    
    # Add edited file path
    op.add_column('photo', sa.Column('edited_path', sa.String(500), nullable=True))


def downgrade():
    # Remove columns in reverse order
    op.drop_column('photo', 'edited_path')
    op.drop_column('photo', 'estimated_year')
    op.drop_column('photo', 'event_name')
    op.drop_column('photo', 'tags')
    op.drop_column('photo', 'description')
    op.drop_column('photo', 'enhancement_settings')
    op.drop_column('photo', 'color_space')
    op.drop_column('photo', 'orientation')
    op.drop_column('photo', 'location_name')
    op.drop_column('photo', 'gps_altitude')
    op.drop_column('photo', 'gps_longitude')
    op.drop_column('photo', 'gps_latitude')
    op.drop_column('photo', 'flash_used')
    op.drop_column('photo', 'focal_length')
    op.drop_column('photo', 'shutter_speed')
    op.drop_column('photo', 'aperture')
    op.drop_column('photo', 'iso')
    op.drop_column('photo', 'camera_model')
    op.drop_column('photo', 'camera_make')
