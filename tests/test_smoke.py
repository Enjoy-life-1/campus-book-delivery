"""冒烟测试：app 导入、健康检查、OpenAPI"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_app_import():
    """Flask app 可正常导入"""
    from app import app
    assert app is not None


def test_health():
    """/api/health 返回 success/ok"""
    from app import app, health_check
    with app.test_request_context('/api/health'):
        r = health_check()
        data = r.get_json()
        assert data.get('status') in ('success', 'ok')


def test_openapi():
    """OpenAPI 3.0 规范存在"""
    from services.engineering import OPENAPI
    assert OPENAPI['openapi'] == '3.0.3'
