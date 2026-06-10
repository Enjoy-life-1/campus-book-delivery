"""baseline schema (create_all + upgrade_db)

Revision ID: 001_baseline
Revises:
Create Date: 2026-06-01

"""
from typing import Sequence, Union

revision: str = '001_baseline'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """占位 revision：实际建表由 init_db / upgrade_db 完成"""
    pass


def downgrade() -> None:
    pass
