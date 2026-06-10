"""创建 MySQL 库 campus_book_delivery 并初始化表与默认账号"""
import os
import time

from _root import setup
setup()

os.environ.setdefault('USE_MYSQL', '1')
os.environ.setdefault('MYSQL_USER', 'root')
os.environ.setdefault('MYSQL_PASSWORD', '123456')
os.environ.setdefault('MYSQL_HOST', '127.0.0.1')
os.environ.setdefault('MYSQL_PORT', '3306')
os.environ.setdefault('MYSQL_DATABASE', 'campus_book_delivery')

from flask import Flask
from database_config import get_sqlalchemy_uri, mysql_connect_kwargs, ensure_mysql_database
from models import db, User
from security import hash_password

DB_NAME = mysql_connect_kwargs()['database']


def create_database():
    """CREATE DATABASE IF NOT EXISTS"""
    name = ensure_mysql_database()
    print(f'数据库 {name or DB_NAME} 已就绪')


def seed_users():
    """默认 admin / student1 测试账号"""
    admin = User.query.filter_by(username='admin').first()
    if admin:
        print('默认用户已存在，跳过')
        return
    ts = time.strftime('%Y-%m-%d %H:%M:%S')
    db.session.add(User(
        id='1', username='admin', password=hash_password('admin123'),
        email='admin@example.com', phone='13800138000',
        created_at=ts, is_admin=True
    ))
    db.session.add(User(
        id='2', username='student1', password=hash_password('student123'),
        email='student1@example.com', phone='13900139000',
        created_at=ts, is_admin=False
    ))
    db.session.commit()
    print('默认账号: admin/admin123  student1/student123')


def main():
    create_database()
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = get_sqlalchemy_uri()
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'pool_pre_ping': True, 'pool_recycle': 3600}
    db.init_app(app)
    with app.app_context():
        db.create_all()
        print('表结构已创建')
        try:
            from upgrade_db import upgrade
            upgrade()
        except Exception as e:
            print(f'升级脚本: {e}')
        seed_users()
    print('MySQL 初始化完成')
    print(f'连接串: {get_sqlalchemy_uri()}')


if __name__ == '__main__':
    main()
