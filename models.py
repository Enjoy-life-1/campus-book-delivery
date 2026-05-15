from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

db = SQLAlchemy()

class User(db.Model):
    """用户表"""
    __tablename__ = 'users'
    
    id = db.Column(db.String(50), primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False, index=True)
    password = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    school = db.Column(db.String(200))
    introduction = db.Column(db.Text)
    avatar = db.Column(db.String(500))
    is_admin = db.Column(db.Boolean, default=False, index=True)
    created_at = db.Column(db.String(50))
    updated_at = db.Column(db.String(50))
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email or '',
            'phone': self.phone or '',
            'school': self.school or '',
            'introduction': self.introduction or '',
            'avatar': self.avatar or '',
            'is_admin': self.is_admin,
            'created_at': self.created_at or ''
        }

class Book(db.Model):
    """书籍表"""
    __tablename__ = 'books'
    
    id = db.Column(db.String(50), primary_key=True)
    title = db.Column(db.String(200), nullable=False, index=True)
    author = db.Column(db.String(100))
    category = db.Column(db.String(50), index=True)
    price = db.Column(db.Float, nullable=False)
    desc = db.Column(db.Text)
    description = db.Column(db.Text)  # 兼容字段
    imgs = db.Column(db.Text)  # JSON 字符串存储图片数组
    image = db.Column(db.String(500))  # 主图片
    cover_url = db.Column(db.String(500))  # 兼容字段
    contact = db.Column(db.String(200))
    stock = db.Column(db.Integer, default=1)
    status = db.Column(db.String(20), default='available', index=True)  # available, sold
    owner_id = db.Column(db.String(50), index=True)
    owner_name = db.Column(db.String(100))
    seller = db.Column(db.String(100))
    sellerId = db.Column(db.String(50))
    createTime = db.Column(db.String(50))
    created_at = db.Column(db.String(50))
    updated_at = db.Column(db.String(50))
    publish_date = db.Column(db.String(50))
    
    def to_dict(self):
        """转换为字典"""
        # 解析 imgs JSON 字符串
        imgs_list = []
        if self.imgs:
            try:
                imgs_list = json.loads(self.imgs) if isinstance(self.imgs, str) else self.imgs
            except:
                imgs_list = [self.imgs] if self.imgs else []
        
        return {
            'id': self.id,
            'title': self.title,
            'author': self.author or '未知作者',
            'category': self.category or 'other',
            'price': float(self.price) if self.price else 0.0,
            'desc': self.desc or '',
            'description': self.description or self.desc or '',
            'imgs': imgs_list,
            'image': self.image or (imgs_list[0] if imgs_list else ''),
            'cover_url': self.cover_url or (imgs_list[0] if imgs_list else ''),
            'contact': self.contact or '',
            'stock': self.stock or 1,
            'status': self.status or 'available',
            'owner_id': self.owner_id or '',
            'owner_name': self.owner_name or '',
            'seller': self.seller or '',
            'sellerId': self.sellerId or '',
            'createTime': self.createTime or '',
            'created_at': self.created_at or '',
            'updated_at': self.updated_at or '',
            'publish_date': self.publish_date or ''
        }

class Order(db.Model):
    """订单表"""
    __tablename__ = 'orders'
    
    id = db.Column(db.String(50), primary_key=True)
    book_id = db.Column(db.String(50), index=True)
    book_title = db.Column(db.String(200))
    buyer_id = db.Column(db.String(50), index=True)
    buyer_name = db.Column(db.String(100))
    seller_id = db.Column(db.String(50), index=True)
    seller_name = db.Column(db.String(100))
    price = db.Column(db.Float)
    status = db.Column(db.String(20), default='pending', index=True)  # pending, completed, cancelled
    created_at = db.Column(db.String(50))
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'book_id': self.book_id,
            'book_title': self.book_title or '',
            'buyer_id': self.buyer_id or '',
            'buyer_name': self.buyer_name or '',
            'seller_id': self.seller_id or '',
            'seller_name': self.seller_name or '',
            'price': float(self.price) if self.price else 0.0,
            'status': self.status or 'pending',
            'created_at': self.created_at or ''
        }

class Collection(db.Model):
    """收藏表"""
    __tablename__ = 'collections'
    
    id = db.Column(db.String(50), primary_key=True)
    book_id = db.Column(db.String(50), index=True)
    user_id = db.Column(db.String(50), index=True)
    username = db.Column(db.String(100))
    created_at = db.Column(db.String(50))
    
    # 唯一约束：同一用户不能重复收藏同一本书
    __table_args__ = (db.UniqueConstraint('book_id', 'user_id', name='unique_user_book_collection'),)
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'book_id': self.book_id,
            'user_id': self.user_id,
            'username': self.username or '',
            'created_at': self.created_at or ''
        }

class CartItem(db.Model):
    """购物车表"""
    __tablename__ = 'cart'
    
    id = db.Column(db.String(50), primary_key=True)
    user_id = db.Column(db.String(50), index=True)
    book_id = db.Column(db.String(50), index=True)
    quantity = db.Column(db.Integer, default=1)
    created_at = db.Column(db.String(50))
    updated_at = db.Column(db.String(50))
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'book_id': self.book_id,
            'quantity': self.quantity or 1,
            'created_at': self.created_at or '',
            'updated_at': self.updated_at or ''
        }

class Setting(db.Model):
    """系统设置表"""
    __tablename__ = 'settings'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.Text)
    updated_at = db.Column(db.String(50))
    
    def to_dict(self):
        """转换为字典"""
        return {
            'key': self.key,
            'value': self.value
        }
    
    @staticmethod
    def get_all_as_dict():
        """获取所有设置并转换为字典"""
        settings = Setting.query.all()
        result = {}
        for setting in settings:
            # 尝试解析 JSON 值
            value = setting.value
            if value:
                try:
                    # 尝试解析为 JSON
                    if value.startswith('{') or value.startswith('['):
                        value = json.loads(value)
                    # 尝试解析为布尔值
                    elif value.lower() == 'true':
                        value = True
                    elif value.lower() == 'false':
                        value = False
                    # 尝试解析为数字
                    elif value.isdigit():
                        value = int(value)
                    elif '.' in value and value.replace('.', '').isdigit():
                        value = float(value)
                except:
                    pass
            result[setting.key] = value
        return result
    
    @staticmethod
    def set_value(key, value):
        """设置值"""
        setting = Setting.query.filter_by(key=key).first()
        if setting:
            # 如果是复杂类型，转换为 JSON
            if isinstance(value, (dict, list, bool)):
                setting.value = json.dumps(value) if isinstance(value, (dict, list)) else str(value).lower()
            else:
                setting.value = str(value)
            setting.updated_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        else:
            # 创建新设置
            value_str = json.dumps(value) if isinstance(value, (dict, list)) else str(value)
            if isinstance(value, bool):
                value_str = str(value).lower()
            setting = Setting(
                key=key,
                value=value_str,
                updated_at=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            )
            db.session.add(setting)
        db.session.commit()

