"""create tools table

Revision ID: 8475035ee19e
Revises: 677cfe19a165
Create Date: 2023-04-02 19:06:32.744660

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8475035ee19e'
down_revision = '677cfe19a165'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'tools',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('added_at', sa.DateTime, nullable=False),
        sa.Column('description', sa.String(150), nullable=False)
    )

def downgrade() -> None:
    op.drop_table('tools')
