"""add foreign key constraints

Revision ID: 002_add_foreign_keys
Revises: 001_baseline
Create Date: 2026-06-01

"""
from typing import Sequence, Union

from alembic import op
from sqlalchemy import inspect

from fk_migration import add_foreign_keys, clean_orphans, drop_foreign_keys

revision: str = '002_add_foreign_keys'
down_revision: Union[str, None] = '001_baseline'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """清理孤儿数据后 batch 添加 FK_SPECS 外键"""
    conn = op.get_bind()
    if 'users' not in inspect(conn).get_table_names():
        return
    clean_orphans(conn)
    add_foreign_keys(op)


def downgrade() -> None:
    """按表逆序删除外键约束"""
    drop_foreign_keys(op)
