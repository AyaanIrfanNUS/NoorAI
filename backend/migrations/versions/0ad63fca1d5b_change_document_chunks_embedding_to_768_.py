"""change document_chunks embedding to 768 dimensions

Revision ID: 0ad63fca1d5b
Revises: 53da05c68091
Create Date: 2026-06-30 13:58:29.055538

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from pgvector.sqlalchemy import Vector


# revision identifiers, used by Alembic.
revision: str = '0ad63fca1d5b'
down_revision: Union[str, Sequence[str], None] = '53da05c68091'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        'document_chunks', 'embedding',
        type_=Vector(768),
        postgresql_using='embedding::text::vector(768)'
    )

def downgrade() -> None:
    op.alter_column(
        'document_chunks', 'embedding',
        type_=Vector(384),
        postgresql_using='embedding::text::vector(384)'
    )