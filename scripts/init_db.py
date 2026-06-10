"""
数据库初始化脚本
用于创建 SQLite 数据库和表结构
"""
from _root import setup
setup()

from flask import Flask
from models import db, User
import hashlib
import time
import os

# 创建 Flask 应用实例
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///campus_book_delivery.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

def hash_password(password):
    """密码哈希"""
    return hashlib.md5(password.encode()).hexdigest()

def init_database():
    """初始化数据库"""
    with app.app_context():
        # 创建所有表
        db.create_all()
        print("数据库表创建成功！")
        
        # 检查是否已有管理员用户
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            # 创建默认管理员账户
            admin_user = User(
                id='1',
                username='admin',
                password=hash_password('admin123'),
                email='admin@example.com',
                phone='13800138000',
                created_at=time.strftime('%Y-%m-%d %H:%M:%S'),
                is_admin=True
            )
            db.session.add(admin_user)
            
            # 创建测试用户
            test_user = User(
                id='2',
                username='student1',
                password=hash_password('student123'),
                email='student1@example.com',
                phone='13900139000',
                created_at=time.strftime('%Y-%m-%d %H:%M:%S'),
                is_admin=False
            )
            db.session.add(test_user)
            
            db.session.commit()
            print("默认用户创建成功！")
            print("管理员账户: admin / admin123")
            print("测试账户: student1 / student123")
        else:
            print("数据库已存在，跳过默认用户创建")

if __name__ == '__main__':
    init_database()

