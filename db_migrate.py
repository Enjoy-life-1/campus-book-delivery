"""Alembic 迁移入口"""
import os

ROOT = os.path.dirname(os.path.abspath(__file__))


def run_migrations():
    """执行 alembic upgrade head"""
    from alembic.config import Config
    from alembic import command
    cfg = Config(os.path.join(ROOT, 'alembic.ini'))
    command.upgrade(cfg, 'head')
