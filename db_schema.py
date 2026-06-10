"""跨 SQLite / MySQL 的数据库 schema 工具（upgrade_db 等使用）"""
from sqlalchemy import text


def dialect_name(engine):
    """当前连接方言：sqlite / mysql 等"""
    return (engine.dialect.name or '').lower()


def column_names(conn, table, engine=None):
    """返回表已有列名集合；SQLite 用 PRAGMA，MySQL 用 INFORMATION_SCHEMA。"""
    engine = engine or conn.engine
    name = dialect_name(engine)
    if name == 'sqlite':
        rows = conn.execute(text(f'PRAGMA table_info({table})')).fetchall()
        return {r[1] for r in rows}
    rows = conn.execute(
        text(
            'SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS '
            'WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = :tbl'
        ),
        {'tbl': table},
    ).fetchall()
    return {r[0] for r in rows}
