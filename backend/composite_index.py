"""Add composite index for clips filtering

Revision ID: add_clip_composite_index
Revises: add_webp_thumbnails
Create Date: 2025-01-XX XX:XX:XX.XXXXXX

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_clip_composite_index'
down_revision = 'add_webp_thumbnails'
branch_labels = None
depends_on = None


def upgrade():
    """
    Dodaje composite index dla często używanych filtrów
    Optymalizuje query: WHERE is_deleted=False ORDER BY created_at
    """

    # Composite index dla is_deleted + created_at
    # Użycie: filtrowanie (is_deleted=False) + sortowanie (created_at DESC)
    op.create_index(
        'idx_clip_deleted_created',
        'clips',
        ['is_deleted', 'created_at'],
        unique=False
    )

    # Composite index dla is_deleted + clip_type + created_at
    # Użycie: filtrowanie po typie + sortowanie
    op.create_index(
        'idx_clip_deleted_type_created',
        'clips',
        ['is_deleted', 'clip_type', 'created_at'],
        unique=False
    )


def downgrade():
    """
    Usuwa composite indexes
    """
    op.drop_index('idx_clip_deleted_type_created', table_name='clips')
    op.drop_index('idx_clip_deleted_created', table_name='clips')