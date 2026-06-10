"""数据库连接配置：支持 SQLite / MySQL

环境变量：
  DATABASE_URL     完整 URI（最高优先级）
  USE_MYSQL=1      启用 MySQL
  MYSQL_*          主机/端口/库名/账号密码
"""
import os
from urllib.parse import quote_plus  # 密码 URL 编码

from sqlalchemy import event
from sqlalchemy.engine import Engine


def get_sqlalchemy_uri():
    """返回 SQLAlchemy 连接 URI，优先 DATABASE_URL，其次 MySQL，默认 SQLite"""
    url = (os.environ.get('DATABASE_URL') or '').strip()
    if url:
        return url  # 一行连接串优先
    if os.environ.get('USE_MYSQL', '').lower() in ('1', 'true', 'yes'):
        user = os.environ.get('MYSQL_USER', 'root')
        password = os.environ.get('MYSQL_PASSWORD', '123456')
        host = os.environ.get('MYSQL_HOST', '127.0.0.1')
        port = os.environ.get('MYSQL_PORT', '3306')
        name = os.environ.get('MYSQL_DATABASE', 'campus_book_delivery')
        pwd = quote_plus(password)  # 特殊字符转义
        return (
            f'mysql+pymysql://{user}:{pwd}@{host}:{port}/{name}'
            f'?charset=utf8mb4'
        )
    return 'sqlite:///campus_book_delivery.db'  # 默认 SQLite 文件


def mysql_connect_kwargs():
    """供 pymysql 直连建库用"""
    return {
        'host': os.environ.get('MYSQL_HOST', '127.0.0.1'),
        'port': int(os.environ.get('MYSQL_PORT', '3306')),
        'user': os.environ.get('MYSQL_USER', 'root'),
        'password': os.environ.get('MYSQL_PASSWORD', '123456'),
        'database': os.environ.get('MYSQL_DATABASE', 'campus_book_delivery'),
    }


def ensure_mysql_database():
    """MySQL 上创建库（不存在时），避免 1049 Unknown database"""
    if os.environ.get('USE_MYSQL', '').lower() not in ('1', 'true', 'yes'):
        return None
    import pymysql
    kw = mysql_connect_kwargs()
    db_name = kw['database']
    conn = pymysql.connect(  # 不指定 database，连服务器
        host=kw['host'],
        port=kw['port'],
        user=kw['user'],
        password=kw['password'],
        charset='utf8mb4',
    )
    try:
        with conn.cursor() as cur:
            cur.execute(
                f"CREATE DATABASE IF NOT EXISTS `{db_name}` "
                "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
        conn.commit()
        return db_name
    finally:
        conn.close()


@event.listens_for(Engine, 'connect')
def _sqlite_enable_foreign_keys(dbapi_conn, connection_record):
    """SQLite 连接时启用外键（默认关闭）"""
    if dbapi_conn.__class__.__module__.startswith('sqlite3'):
        cursor = dbapi_conn.cursor()
        cursor.execute('PRAGMA foreign_keys=ON')
        cursor.close()


def enable_sqlite_foreign_keys(engine):
    """Alembic 迁移时启用 SQLite 外键（与 connect 事件二选一场景）"""
    if engine.dialect.name == 'sqlite':
        @event.listens_for(engine, 'connect')
        def _fk(dbapi_conn, connection_record):
            cursor = dbapi_conn.cursor()
            cursor.execute('PRAGMA foreign_keys=ON')
            cursor.close()
