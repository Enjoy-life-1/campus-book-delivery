"""体验与工程：OpenAPI 文档、Redis/内存缓存"""
import os

from flask import jsonify, render_template_string
from flask_caching import Cache

OPENAPI = {
    'openapi': '3.0.3',
    'info': {
        'title': '校园书递 API',
        'version': '1.0.0',
        'description': '校园二手书交易平台 REST 接口（核心路径）'
    },
    'servers': [{'url': '/api'}],
    'paths': {
        '/health': {'get': {'summary': '健康检查', 'tags': ['系统']}},
        '/login': {'post': {'summary': '登录', 'tags': ['认证']}},
        '/register': {'post': {'summary': '注册', 'tags': ['认证']}},
        '/books': {
            'get': {'summary': '书籍列表', 'tags': ['书籍']},
            'post': {'summary': '发布书籍', 'tags': ['书籍']}
        },
        '/books/{book_id}': {
            'get': {'summary': '书籍详情', 'tags': ['书籍']},
            'put': {'summary': '更新书籍', 'tags': ['书籍']}
        },
        '/orders': {
            'get': {'summary': '我的订单', 'tags': ['订单']},
            'post': {'summary': '创建订单', 'tags': ['订单']}
        },
        '/collections': {'get': {'summary': '我的收藏', 'tags': ['收藏']}},
        '/conversations': {'get': {'summary': '私信会话', 'tags': ['私信']}},
        '/campus/verify': {'post': {'summary': '学籍认证', 'tags': ['校园']}},
        '/admin/stats': {'get': {'summary': '管理统计', 'tags': ['管理']}},
        '/openapi.json': {'get': {'summary': 'OpenAPI 规范', 'tags': ['系统']}}
    }
}

DOCS_HTML = '''<!DOCTYPE html>
<html lang="zh-CN"><head>
<meta charset="UTF-8"><title>校园书递 API</title>
<link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist@5/swagger-ui.css">
</head><body>
<div id="swagger-ui"></div>
<script src="https://unpkg.com/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
<script>SwaggerUIBundle({url:"/api/openapi.json",dom_id:"#swagger-ui"})</script>
</body></html>'''


def build_cache_config():
    """Redis 可用则用 RedisCache，否则 SimpleCache（分类/公告缓存）"""
    redis_url = (os.environ.get('REDIS_URL') or os.environ.get('CACHE_REDIS_URL') or '').strip()
    if redis_url:
        return {
            'CACHE_TYPE': 'RedisCache',
            'CACHE_REDIS_URL': redis_url,
            'CACHE_DEFAULT_TIMEOUT': 120,
        }
    return {'CACHE_TYPE': 'SimpleCache', 'CACHE_DEFAULT_TIMEOUT': 120}


cache = Cache(config=build_cache_config())


def register_engineering(app):
    """Swagger UI + OpenAPI JSON"""
    @app.route('/api/openapi.json', methods=['GET'])
    def openapi_json():
        return jsonify(OPENAPI)

    @app.route('/api/docs', methods=['GET'])
    def api_docs():
        return render_template_string(DOCS_HTML)
