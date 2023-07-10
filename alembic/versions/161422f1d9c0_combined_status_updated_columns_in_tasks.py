"""Combined status_updated columns in tasks

Revision ID: 161422f1d9c0
Revises: 32e4b2aa88f4
Create Date: 2023-05-22 16:19:26.400108

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '161422f1d9c0'
down_revision = '32e4b2aa88f4'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.drop_column('tasks', 'approved_at')
    op.drop_column('tasks', 'rejected_at')
    op.drop_column('tasks', 'finished_at')
    op.add_column('tasks', sa.Column('status_updated_at', sa.DateTime))
    op.execute('ALTER TABLE tasks MODIFY COLUMN status_updated_at DATETIME AFTER created_at')

def downgrade() -> None:
    op.drop_column('tasks', 'status_updated_at')
    op.add_column('tasks', sa.Column('approved_at', sa.DateTime))
    op.add_column('tasks', sa.Column('rejected_at', sa.DateTime))
    op.add_column('tasks', sa.Column('finished_at', sa.DateTime))
