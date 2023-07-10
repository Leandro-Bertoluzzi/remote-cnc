"""Reordered columns in tasks table

Revision ID: 32e4b2aa88f4
Revises: bb56f0eca8c5
Create Date: 2023-05-22 13:24:26.032792

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '32e4b2aa88f4'
down_revision = 'bb56f0eca8c5'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Tasks
    op.execute('ALTER TABLE tasks MODIFY COLUMN name VARCHAR(50) AFTER id')
    op.execute('ALTER TABLE tasks MODIFY COLUMN user_id INTEGER AFTER priority')
    op.execute('ALTER TABLE tasks MODIFY COLUMN file_id INTEGER AFTER user_id')
    op.execute('ALTER TABLE tasks MODIFY COLUMN tool_id INTEGER AFTER file_id')
    op.execute('ALTER TABLE tasks MODIFY COLUMN material_id INTEGER AFTER tool_id')
    op.execute('ALTER TABLE tasks MODIFY COLUMN note VARCHAR(150) AFTER material_id')

def downgrade() -> None:
    return
