# Flask 后端入口：加载配置、注册路由、启动开发服务器
from flask import Flask, request, jsonify, session  # Web 框架、请求对象、JSON 响应、Session
from flask_cors import CORS  # 跨域，开发时 Vue(5173) 访问 API(5000)
import os  # 环境变量
import time  # 时间戳

from services.admin_compliance import is_staff_user  # 判断是否管理员/版主
from database_config import get_sqlalchemy_uri  # SQLite 或 MySQL 连接串
from services.engineering import cache, register_engineering  # 缓存与 OpenAPI 文档
from models import db, User  # ORM 与用户模型
from security import hash_password, verify_password  # 密码哈希与校验
from app_helpers import (
    BASE_DIR, DIST_DIR, MESSAGE_UPLOAD_DIR, MSG_AUDIO_EXT, MSG_IMAGE_EXT,
    _gateway_url, build_route_helpers, generate_id, is_admin, is_full_admin,
    is_logged_in, push_notification, send_channel_message, sms_channel_configured,
)  # 公共工具函数
from routes import register_all_routes  # 统一注册所有 HTTP 路由


def _load_env_file():
    """启动前将 .env 载入 os.environ"""
    root = os.path.dirname(os.path.abspath(__file__))  # 项目根目录
    try:
        from dotenv import load_dotenv
        load_dotenv(os.path.join(root, '.env'), override=False)  # 不覆盖已有系统变量
        return
    except ImportError:
        pass  # 无 dotenv 库则手动解析
    env_path = os.path.join(root, '.env')
    if not os.path.isfile(env_path):
        return
    try:
        with open(env_path, encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#') or '=' not in line:
                    continue  # 跳过空行、注释
                key, val = line.split('=', 1)
                key, val = key.strip(), val.strip().strip('"').strip("'")
                if key and key not in os.environ:
                    os.environ[key] = val
    except OSError:
        pass


_load_env_file()  # 模块加载时立即执行

app = Flask(__name__, static_folder='static', template_folder='templates')  # 创建 Flask 应用
_DEFAULT_SECRET = 'dev-campus-book-delivery-change-me'  # 开发默认密钥
app.config['SECRET_KEY'] = (
    os.environ.get('SECRET_KEY') or os.environ.get('FLASK_SECRET_KEY') or _DEFAULT_SECRET
)  # Session 签名密钥
if app.config['SECRET_KEY'] in ('your-secret-key', _DEFAULT_SECRET):
    if os.environ.get('FLASK_ENV', '').lower() == 'production':
        raise RuntimeError('生产环境必须设置环境变量 SECRET_KEY（不可用默认值）')
    print('[WARN] 请设置环境变量 SECRET_KEY，勿在生产环境使用默认值')
app.config['SQLALCHEMY_DATABASE_URI'] = get_sqlalchemy_uri()  # 数据库 URI
if get_sqlalchemy_uri().startswith('mysql'):
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'pool_pre_ping': True, 'pool_recycle': 3600}  # MySQL 连接池
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # 关闭 ORM 修改追踪
_cors_origins = os.environ.get('CORS_ORIGINS', '').strip()  # 生产跨域白名单
if _cors_origins:
    CORS(app, supports_credentials=True, origins=[o.strip() for o in _cors_origins.split(',') if o.strip()])
else:
    CORS(app, supports_credentials=True)  # 开发：允许任意来源 + Cookie

DIST_ASSETS_DIR = os.path.join(DIST_DIR, 'assets')  # Vue 打包 JS/CSS 目录

db.init_app(app)  # 绑定 SQLAlchemy
register_engineering(app)  # /api/docs、/api/openapi.json
cache.init_app(app)  # Flask-Caching
from services.engineering import build_cache_config as _build_cache_config
print(f'[INFO] 缓存后端: {_build_cache_config().get("CACHE_TYPE", "SimpleCache")}')


@app.after_request
def add_security_headers(response):
    """全局安全响应头"""
    response.headers['X-Content-Type-Options'] = 'nosniff'  # 防 MIME 嗅探
    return response


@app.before_request
def _sync_admin_session_flag():
    """每次请求同步 session 中的 is_admin 与数据库一致"""
    if 'user_id' not in session:
        return
    flag = is_admin()
    if session.get('is_admin') != flag:
        session['is_admin'] = flag
        session.modified = True


@app.before_request
def _guard_admin_api():
    """拦截非管理员的 /api/admin/* 请求"""
    path = request.path or ''
    if not path.startswith('/api/admin/') or path == '/api/admin/login':
        return  # 非管理 API 或登录接口放行
    if request.method == 'OPTIONS':
        return  # CORS 预检
    if not is_admin():
        return jsonify({'status': 'error', 'message': '无管理权限'}), 403


@app.route('/static/<path:filename>')
def static_cached(filename):
    """静态资源：CSS/JS/图片长缓存"""
    response = app.send_static_file(filename)
    if filename.endswith(('.css', '.js', '.jpg', '.jpeg', '.png', '.gif')):
        response.headers['Cache-Control'] = 'max-age=31536000, immutable'  # 静态资源长缓存
    return response


_auth_handlers = register_all_routes(  # 注册全部业务路由
    app,
    build_route_helpers(app),
    {
        'dist_assets_dir': DIST_ASSETS_DIR,
        'is_staff_user': is_staff_user,
        'gateway_url': _gateway_url,
        'send_channel_message': send_channel_message,
    },
)
health_check = _auth_handlers['health_check']  # 供测试引用
login = _auth_handlers['login']
logout = _auth_handlers['logout']
get_user_info = _auth_handlers['get_user_info']


def bootstrap_database():
    """启动时建库、迁移、种子用户"""
    if get_sqlalchemy_uri().startswith('mysql'):
        from database_config import ensure_mysql_database
        db_name = ensure_mysql_database()  # 库不存在则 CREATE DATABASE
        print(f'[INFO] MySQL database ready: {db_name}')
    with app.app_context():  # ORM 需要应用上下文
        db.create_all()  # 按 models 建表
        try:
            from upgrade_db import upgrade
            upgrade()
        except Exception as e:
            print(f'[WARN] upgrade_db skipped: {e}')
        try:
            from db_migrate import run_migrations
            run_migrations()  # Alembic 迁移
        except Exception as e:
            print(f'[WARN] alembic migrate skipped: {e}')
        if User.query.filter_by(username='admin').first():
            return  # 已有 admin 跳过种子
        db.session.add(User(  # 默认管理员
            id='1', username='admin', password=hash_password('admin123'),
            email='admin@example.com', phone='13800138000',
            created_at=time.strftime('%Y-%m-%d %H:%M:%S'), is_admin=True,
        ))
        db.session.add(User(  # 默认测试学生
            id='2', username='student1', password=hash_password('student123'),
            email='student1@example.com', phone='13900139000',
            created_at=time.strftime('%Y-%m-%d %H:%M:%S'), is_admin=False,
        ))
        db.session.commit()
        print('[INFO] created default users: admin / student1')
    check_security_warnings()


def check_security_warnings():
    """生产环境安全检查"""
    if os.environ.get('FLASK_ENV', '').lower() != 'production':
        return
    with app.app_context():
        admin = User.query.filter_by(username='admin').first()
        if admin and verify_password('admin123', admin.password):
            print('[WARN] 生产环境 admin 仍为默认密码 admin123，请立即修改')
        if not sms_channel_configured():
            print('[WARN] 生产环境未配置短信（阿里云 SMS 或 SMS_WEBHOOK_URL），注册/找回密码不可用')


def check_database():
    """探测数据库是否可连接"""
    from sqlalchemy import text
    uri = get_sqlalchemy_uri()
    with app.app_context():
        try:
            db.session.execute(text('SELECT 1'))
            shown = uri.split('@')[-1] if '@' in uri else uri  # 日志隐藏密码
            print(f'[INFO] database OK: {shown}')
            return True
        except Exception as e:
            print(f'[ERROR] database connection failed: {e}')
            print('[HINT] 请运行 本机部署.bat 或检查 .env 数据库配置')
            print('[HINT] start MySQL and fix MYSQL_PASSWORD in .env')
            return False


if __name__ == '__main__':  # python app.py 直接运行
    bootstrap_database()
    if not check_database():
        raise SystemExit(1)
    app.run(debug=True, host='0.0.0.0', port=5000)  # 开发服务器，监听 5000
