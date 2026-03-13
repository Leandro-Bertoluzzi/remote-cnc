"""add fks to tasks table

Revision ID: 677cfe19a165
Revises: b45f388692dc
Create Date: 2023-04-02 18:49:50.476468

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '677cfe19a165'
down_revision = 'b45f388692dc'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('tasks', sa.Column('user_id', sa.Integer, nullable=False))
    op.add_column('tasks', sa.Column('file_id', sa.Integer, nullable=False))

    op.create_foreign_key(
        "fk_owner_id",
        "tasks",
        "users",
        ["user_id"],
        ["id"],
        ondelete='CASCADE'
    )
    op.create_foreign_key(
        "fk_file_id",
        "tasks",
        "files",
        ["file_id"],
        ["id"]
    )


def downgrade() -> None:
    op.drop_constraint('fk_owner_id', 'tasks', type_='foreignkey')
    op.drop_column('tasks', 'user_id')
    op.drop_constraint('fk_file_id', 'tasks', type_='foreignkey')
    op.drop_column('tasks', 'file_id')
