"""create tools table

Revision ID: 8475035ee19e
Revises: 677cfe19a165
Create Date: 2023-04-02 19:06:32.744660

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import func


# revision identifiers, used by Alembic.
revision = '8475035ee19e'
down_revision = '677cfe19a165'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'tools',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('name', sa.String(50), nullable=False),
        sa.Column('description', sa.String(150), nullable=False),
        sa.Column('added_at', sa.DateTime, nullable=False, server_default=func.now())
    )


def downgrade() -> None:
    op.drop_table('tools')
