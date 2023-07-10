"""Add inventory fks to tasks table

Revision ID: 8c8c413bf8ac
Revises: 6d8972b34033
Create Date: 2023-05-15 17:52:02.017264

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '8c8c413bf8ac'
down_revision = '6d8972b34033'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.add_column('tasks', sa.Column('tool_id', sa.Integer, nullable=False))
    op.add_column('tasks', sa.Column('material_id', sa.Integer, nullable=False))

    op.create_foreign_key(
        "fk_tool_id",
        "tasks",
        "tools",
        ["tool_id"],
        ["id"]
    )
    op.create_foreign_key(
        "fk_material_id",
        "tasks",
        "materials",
        ["material_id"],
        ["id"]
    )


def downgrade() -> None:
    op.drop_constraint('fk_tool_id', 'tasks', type_='foreignkey')
    op.drop_column('tasks', 'tool_id')
    op.drop_constraint('fk_material_id', 'tasks', type_='foreignkey')
    op.drop_column('tasks', 'material_id')

