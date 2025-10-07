"""Add thumbnail_webp_path to clips

Revision ID: add_webp_thumbnails
Revises: <previous_revision>
Create Date: 2025-01-XX XX:XX:XX.XXXXXX

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_webp_thumbnails'
down_revision = '<previous_revision>'  # Ustaw na ostatnią rewizję
branch_labels = None
depends_on = None


def upgrade():
    """
    Dodaje kolumnę thumbnail_webp_path do tabeli clips
    """
    # Dodaj nową kolumnę
    op.add_column(
        'clips',
        sa.Column('thumbnail_webp_path', sa.String(), nullable=True)
    )

    # Dodaj index dla szybszego wyszukiwania
    op.create_index(
        'ix_clips_thumbnail_webp_path',
        'clips',
        ['thumbnail_webp_path'],
        unique=False
    )


def downgrade():
    """
    Usuwa kolumnę thumbnail_webp_path z tabeli clips
    """
    # Usuń index
    op.drop_index('ix_clips_thumbnail_webp_path', table_name='clips')

    # Usuń kolumnę
    op.drop_column('clips', 'thumbnail_webp_path')