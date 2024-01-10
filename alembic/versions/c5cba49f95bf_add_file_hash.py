"""Add file hash

Revision ID: c5cba49f95bf
Revises: ef375042cb3f
Create Date: 2024-01-10 17:20:47.762285

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c5cba49f95bf'
down_revision = 'ef375042cb3f'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_column('files', 'file_path')
    op.add_column('files', sa.Column('file_hash', sa.String(150)))


def downgrade() -> None:
    op.drop_column('files', 'file_hash')
    op.add_column('files', sa.Column('file_path', sa.String(150)))
