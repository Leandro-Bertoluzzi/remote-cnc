"""add file analysis

Revision ID: 46ab6ab25408
Revises: 5269cf543947
Create Date: 2024-09-17 20:41:08.829916

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


# revision identifiers, used by Alembic.
revision = '46ab6ab25408'
down_revision = '5269cf543947'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('files', sa.Column('report', JSONB))


def downgrade() -> None:
    op.drop_column('files', 'report')
