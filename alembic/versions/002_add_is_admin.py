"""Add is_admin column to users table

Revision ID: 002_add_is_admin
Revises: 001_initial
Create Date: 2026-01-28 01:04:30.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '002_add_is_admin'
down_revision = '001_initial'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Добавляем колонку is_admin в таблицу users
    op.add_column('users', sa.Column('is_admin', sa.Boolean(), nullable=False, server_default='false'))


def downgrade() -> None:
    # При откате удаляем колонку is_admin
    op.drop_column('users', 'is_admin')
