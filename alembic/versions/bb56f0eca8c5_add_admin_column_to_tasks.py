"""Add admin column to tasks

Revision ID: bb56f0eca8c5
Revises: 8c8c413bf8ac
Create Date: 2023-05-22 12:46:47.415272

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'bb56f0eca8c5'
down_revision = '8c8c413bf8ac'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('tasks', sa.Column('admin_id', sa.Integer))
    op.create_foreign_key(
        "fk_admin_id",
        "tasks",
        "users",
        ["admin_id"],
        ["id"]
    )


def downgrade() -> None:
    op.drop_constraint('fk_admin_id', 'tasks', type_='foreignkey')
    op.drop_column('tasks', 'admin_id')
