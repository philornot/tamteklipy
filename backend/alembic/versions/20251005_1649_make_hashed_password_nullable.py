"""make hashed_password nullable

Revision ID: make_hashed_password_nullable_20251005_1649
Revises: 6e60772a485d
Create Date: 2025-10-05 16:49:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'make_hashed_password_nullable_20251005_1649'
down_revision: Union[str, Sequence[str], None] = '6e60772a485d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # SQLite wymaga batch_alter_table dla ALTER COLUMN
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.alter_column('hashed_password',
                              existing_type=sa.String(length=255),
                              nullable=True)


def downgrade() -> None:
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.alter_column('hashed_password',
                              existing_type=sa.String(length=255),
                              nullable=False)

