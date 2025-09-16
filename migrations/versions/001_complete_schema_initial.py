"""Complete schema with Album, Person, and PhotoPerson models

Revision ID: 001_complete_schema_initial
Revises: 
Create Date: 2025-09-13 10:12:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '001_complete_schema_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create Album table
    op.create_table('album',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('date_start', sa.Date(), nullable=True),
        sa.Column('date_end', sa.Date(), nullable=True),
        sa.Column('time_period', sa.String(length=100), nullable=True),
        sa.Column('location', sa.String(length=200), nullable=True),
        sa.Column('event_type', sa.String(length=100), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create Person table
    op.create_table('person',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('nickname', sa.String(length=100), nullable=True),
        sa.Column('birth_year', sa.Integer(), nullable=True),
        sa.Column('relationship', sa.String(length=100), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create PhotoPerson association table with face detection metadata
    op.create_table('photo_people',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('photo_id', sa.Integer(), nullable=False),
        sa.Column('person_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.Column('face_box_x', sa.Integer(), nullable=True),
        sa.Column('face_box_y', sa.Integer(), nullable=True),
        sa.Column('face_box_width', sa.Integer(), nullable=True),
        sa.Column('face_box_height', sa.Integer(), nullable=True),
        sa.Column('manually_tagged', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('verified', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('notes', sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(['person_id'], ['person.id'], ),
        sa.ForeignKeyConstraint(['photo_id'], ['photo.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('photo_id', 'person_id', name='unique_photo_person')
    )

    # Add enhanced columns to Photo table
    with op.batch_alter_table('photo', schema=None) as batch_op:
        batch_op.add_column(sa.Column('album_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('photo_date', sa.Date(), nullable=True))
        batch_op.add_column(sa.Column('date_text', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('date_circa', sa.Boolean(), nullable=False, server_default='false'))
        batch_op.add_column(sa.Column('location_text', sa.String(length=200), nullable=True))
        batch_op.add_column(sa.Column('occasion', sa.String(length=200), nullable=True))
        batch_op.add_column(sa.Column('condition', sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column('photo_source', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('back_text', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('needs_restoration', sa.Boolean(), nullable=False, server_default='false'))
        batch_op.add_column(sa.Column('auto_enhanced', sa.Boolean(), nullable=False, server_default='false'))
        batch_op.add_column(sa.Column('processing_notes', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('paired_photo_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('is_back_side', sa.Boolean(), nullable=False, server_default='false'))
        batch_op.create_foreign_key('fk_photo_album_id', 'album', ['album_id'], ['id'])
        batch_op.create_foreign_key('fk_photo_paired_photo_id', 'photo', ['paired_photo_id'], ['id'])


def downgrade():
    # Drop enhanced columns from Photo table
    with op.batch_alter_table('photo', schema=None) as batch_op:
        batch_op.drop_constraint('fk_photo_paired_photo_id', type_='foreignkey')
        batch_op.drop_constraint('fk_photo_album_id', type_='foreignkey')
        batch_op.drop_column('is_back_side')
        batch_op.drop_column('paired_photo_id')
        batch_op.drop_column('processing_notes')
        batch_op.drop_column('auto_enhanced')
        batch_op.drop_column('needs_restoration')
        batch_op.drop_column('back_text')
        batch_op.drop_column('photo_source')
        batch_op.drop_column('condition')
        batch_op.drop_column('occasion')
        batch_op.drop_column('location_text')
        batch_op.drop_column('date_circa')
        batch_op.drop_column('date_text')
        batch_op.drop_column('photo_date')
        batch_op.drop_column('album_id')

    # Drop tables
    op.drop_table('photo_people')
    op.drop_table('person')
    op.drop_table('album')