"""Add unique constraint for user email

Revision ID: 47f8b3a7f591
Revises: 8475035ee19e
Create Date: 2023-05-10 20:56:07.899969

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '47f8b3a7f591'
down_revision = '8475035ee19e'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_unique_constraint("unique_users_email", "users", ["email"])

def downgrade() -> None:
    op.drop_constraint("unique_users_email", "users", type_="unique")
