"""db_schema 工具与鉴权 API 基础测试"""
import os
import sys

import pytest
from sqlalchemy import create_engine, text

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db_schema import column_names, dialect_name


def _status(resp):
    if isinstance(resp, tuple):
        return resp[1]
    return resp.status_code


def _json(resp):
    body = resp[0] if isinstance(resp, tuple) else resp
    return body.get_json()


def test_column_names_sqlite():
    """column_names 在 SQLite 内存库可用"""
    eng = create_engine('sqlite:///:memory:')
    with eng.connect() as conn:
        conn.execute(text('CREATE TABLE demo (id TEXT, title VARCHAR(200))'))
        conn.commit()
        cols = column_names(conn, 'demo', eng)
    assert cols == {'id', 'title'}
    assert dialect_name(eng) == 'sqlite'


def test_user_info_requires_login():
    """未登录 /api/user/info → 401"""
    from app import app, get_user_info
    with app.test_request_context('/api/user/info', method='GET'):
        r = get_user_info()
        assert _status(r) == 401


def test_login_wrong_password():
    """错误密码登录 → 401"""
    from app import app, login
    with app.test_request_context(
        '/api/login', method='POST', json={'username': 'nobody', 'password': 'wrong'}
    ):
        r = login()
        assert _status(r) == 401
        assert _json(r).get('status') == 'error'


def test_logout_ok():
    """登出成功"""
    from app import app, logout
    with app.test_request_context('/api/logout', method='POST'):
        r = logout()
        assert _status(r) == 200
        assert _json(r).get('status') == 'success'
