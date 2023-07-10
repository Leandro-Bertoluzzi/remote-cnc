"""Create materials table

Revision ID: f0fe8ee5571c
Revises: 47f8b3a7f591
Create Date: 2023-05-14 15:28:34.293584

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import func

# revision identifiers, used by Alembic.
revision = 'f0fe8ee5571c'
down_revision = '47f8b3a7f591'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'materials',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('name', sa.String(50), nullable=False),
        sa.Column('description', sa.String(150), nullable=False),
        sa.Column('added_at', sa.DateTime, nullable=False, server_default=func.now())
    )

def downgrade():
    op.drop_table('materials')
