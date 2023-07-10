"""Add name for tasks

Revision ID: 6d8972b34033
Revises: f0fe8ee5571c
Create Date: 2023-05-15 14:26:46.275841

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '6d8972b34033'
down_revision = 'f0fe8ee5571c'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('tasks', sa.Column('name', sa.String(50), nullable=False))
    op.add_column('tasks', sa.Column('note', sa.String(150)))

def downgrade():
    op.drop_column('tasks', 'name')
    op.drop_column('tasks', 'note')
