"""Initial migration: create all tables

Revision ID: 001_initial
Revises: 
Create Date: 2026-01-28 01:04:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Эта миграция только документирует существующую схему
    # Таблицы уже существуют в БД
    pass


def downgrade() -> None:
    # При откате не удаляем таблицы, так как они могут содержать данные
    pass
