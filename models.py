# ORM 模型定义：用户、书籍、订单及社区相关表
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

db = SQLAlchemy()  # 全局数据库对象，在 app.py 中 init_app


def fk(table, ondelete='SET NULL'):
    """外键辅助：ondelete 可为 CASCADE（删父删子）或 SET NULL"""
    return db.ForeignKey(f'{table}.id', ondelete=ondelete)

class User(db.Model):
    """用户表：账号、校区、封禁、学籍认证、通知偏好"""
    __tablename__ = 'users'
    
    id = db.Column(db.String(50), primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False, index=True)
    password = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    school = db.Column(db.String(200))
    campus_zone = db.Column(db.String(100), default='西校区')
    dorm_building = db.Column(db.String(50))
    introduction = db.Column(db.Text)
    avatar = db.Column(db.String(500))
    is_admin = db.Column(db.Boolean, default=False, index=True)
    role = db.Column(db.String(20), default='student', index=True)  # student / moderator / admin
    ban_level = db.Column(db.String(20), default='none', index=True)  # none / warning / mute / ban
    ban_until = db.Column(db.String(50))
    ban_reason = db.Column(db.Text)
    notify_email = db.Column(db.Boolean, default=True)
    notify_sms = db.Column(db.Boolean, default=True)
    subscribe_price_drop = db.Column(db.Boolean, default=True)
    schedule_json = db.Column(db.Text)
    no_show_count = db.Column(db.Integer, default=0)
    school_id = db.Column(db.String(50), fk('campus_schools'), index=True)
    student_id = db.Column(db.String(50))
    campus_email = db.Column(db.String(120))
    campus_verified = db.Column(db.Boolean, default=False, index=True)
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
            'school_id': self.school_id or '',
            'student_id': self.student_id or '',
            'campus_email': self.campus_email or '',
            'campus_verified': bool(self.campus_verified),
            'campus_zone': self.campus_zone or '西校区',
            'dorm_building': self.dorm_building or '',
            'introduction': self.introduction or '',
            'avatar': self.avatar or '',
            'is_admin': self.is_admin,
            'role': self.effective_role(),
            'ban_level': self.ban_level or 'none',
            'ban_until': self.ban_until or '',
            'ban_reason': self.ban_reason or '',
            'notify_email': bool(self.notify_email),
            'notify_sms': bool(self.notify_sms),
            'subscribe_price_drop': bool(self.subscribe_price_drop),
            'created_at': self.created_at or ''
        }

    def effective_role(self):
        """返回有效角色：is_admin 优先于 role 字段"""
        if self.is_admin:
            return 'admin'
        return self.role or 'student'

class Book(db.Model):
    """书籍表：在售信息、校区、降价、套装、审核状态 status"""
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
    owner_id = db.Column(db.String(50), fk('users'), index=True)
    owner_name = db.Column(db.String(100))
    seller = db.Column(db.String(100))
    sellerId = db.Column(db.String(50), fk('users'))
    createTime = db.Column(db.String(50))
    created_at = db.Column(db.String(50))
    updated_at = db.Column(db.String(50))
    publish_date = db.Column(db.String(50))
    condition = db.Column(db.String(50))  # 成色：全新/九成新/八成新等
    isbn = db.Column(db.String(30), index=True)
    edition = db.Column(db.String(80))
    course_code = db.Column(db.String(50), index=True)
    campus_zone = db.Column(db.String(100))
    dorm_building = db.Column(db.String(50), index=True)
    campaign_tag = db.Column(db.String(50), index=True)
    original_price = db.Column(db.Float)
    price_drop_until = db.Column(db.String(50))
    price_drop_plan = db.Column(db.Text)
    listing_type = db.Column(db.String(20), default='single')  # single / bundle
    bundle_items = db.Column(db.Text)
    view_count = db.Column(db.Integer, default=0)
    school_id = db.Column(db.String(50), fk('campus_schools'), index=True)

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
            'publish_date': self.publish_date or '',
            'condition': self.condition or '',
            'isbn': self.isbn or '',
            'edition': self.edition or '',
            'course_code': self.course_code or '',
            'campus_zone': self.campus_zone or '',
            'dorm_building': self.dorm_building or '',
            'campaign_tag': self.campaign_tag or '',
            'original_price': float(self.original_price) if self.original_price else None,
            'price_drop_until': self.price_drop_until or '',
            'price_drop_plan': self._json_load(self.price_drop_plan),
            'listing_type': self.listing_type or 'single',
            'bundle_items': self._json_load(self.bundle_items) or [],
            'view_count': int(self.view_count or 0),
            'school_id': self.school_id or ''
        }

    @staticmethod
    def _json_load(raw):
        """TEXT 列 JSON 安全解析"""
        if not raw:
            return None
        try:
            return json.loads(raw) if isinstance(raw, str) else raw
        except (json.JSONDecodeError, TypeError):
            return None

class Category(db.Model):
    """书籍分类表"""
    __tablename__ = 'categories'

    id = db.Column(db.String(50), primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    sort_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.String(50))

    def to_dict(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'sort_order': self.sort_order or 0,
            'created_at': self.created_at or ''
        }

class Announcement(db.Model):
    """系统公告表"""
    __tablename__ = 'announcements'

    id = db.Column(db.String(50), primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(30), default='guide')  # rule / guide / safety
    is_active = db.Column(db.Boolean, default=True, index=True)
    created_at = db.Column(db.String(50))
    updated_at = db.Column(db.String(50))

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'type': self.type or 'guide',
            'is_active': self.is_active,
            'created_at': self.created_at or '',
            'updated_at': self.updated_at or ''
        }

class Order(db.Model):
    """订单表：买卖家、面交状态、购买/换书 order_type"""
    __tablename__ = 'orders'
    
    id = db.Column(db.String(50), primary_key=True)
    book_id = db.Column(db.String(50), fk('books'), index=True)
    book_title = db.Column(db.String(200))
    buyer_id = db.Column(db.String(50), fk('users'), index=True)
    buyer_name = db.Column(db.String(100))
    seller_id = db.Column(db.String(50), fk('users'), index=True)
    seller_name = db.Column(db.String(100))
    price = db.Column(db.Float)
    status = db.Column(db.String(20), default='pending', index=True)  # pending, pickup, completed, cancelled
    cancel_reason = db.Column(db.String(300))
    order_type = db.Column(db.String(20), default='sale', index=True)  # sale / exchange
    exchange_book_title = db.Column(db.String(200))
    exchange_note = db.Column(db.Text)
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
            'cancel_reason': self.cancel_reason or '',
            'order_type': self.order_type or 'sale',
            'exchange_book_title': self.exchange_book_title or '',
            'exchange_note': self.exchange_note or '',
            'created_at': self.created_at or ''
        }

class Collection(db.Model):
    """收藏表：collected_price 用于降价提醒"""
    __tablename__ = 'collections'
    
    id = db.Column(db.String(50), primary_key=True)
    book_id = db.Column(db.String(50), fk('books', 'CASCADE'), index=True)
    user_id = db.Column(db.String(50), fk('users', 'CASCADE'), index=True)
    username = db.Column(db.String(100))
    collected_price = db.Column(db.Float)  # 收藏时价格，用于降价提醒
    price_alert = db.Column(db.Boolean, default=True)
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
            'collected_price': float(self.collected_price) if self.collected_price else None,
            'price_alert': bool(self.price_alert),
            'created_at': self.created_at or ''
        }

class CartItem(db.Model):
    """购物车表：user_id + book_id 多本数量"""
    __tablename__ = 'cart'
    
    id = db.Column(db.String(50), primary_key=True)
    user_id = db.Column(db.String(50), fk('users', 'CASCADE'), index=True)
    book_id = db.Column(db.String(50), fk('books', 'CASCADE'), index=True)
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

class Comment(db.Model):
    """书籍评论表；audit_status 控制前台展示"""
    __tablename__ = 'comments'

    id = db.Column(db.String(50), primary_key=True)
    book_id = db.Column(db.String(50), fk('books', 'CASCADE'), index=True, nullable=False)
    book_title = db.Column(db.String(200))
    user_id = db.Column(db.String(50), fk('users', 'CASCADE'), index=True, nullable=False)
    username = db.Column(db.String(100))
    content = db.Column(db.Text, nullable=False)
    likes = db.Column(db.Integer, default=0)
    is_deleted = db.Column(db.Boolean, default=False, index=True)
    audit_status = db.Column(db.String(20), default='approved', index=True)  # pending / approved / rejected
    created_at = db.Column(db.String(50))

    def to_dict(self):
        return {
            'id': self.id,
            'book_id': self.book_id,
            'book_title': self.book_title or '',
            'user_id': self.user_id,
            'username': self.username or '',
            'content': self.content or '',
            'likes': self.likes or 0,
            'is_deleted': bool(self.is_deleted),
            'audit_status': self.audit_status or 'approved',
            'created_at': self.created_at or ''
        }


class Review(db.Model):
    """订单评价表"""
    __tablename__ = 'reviews'

    id = db.Column(db.String(50), primary_key=True)
    order_id = db.Column(db.String(50), fk('orders', 'CASCADE'), index=True, nullable=False)
    book_id = db.Column(db.String(50), fk('books'), index=True)
    reviewer_id = db.Column(db.String(50), fk('users', 'CASCADE'), index=True, nullable=False)
    reviewer_name = db.Column(db.String(100))
    reviewer_role = db.Column(db.String(20))  # buyer / seller
    reviewed_user_id = db.Column(db.String(50), fk('users'), index=True)
    description_rating = db.Column(db.Integer, default=5)  # 描述相符
    service_rating = db.Column(db.Integer, default=5)  # 态度/服务
    condition_rating = db.Column(db.Integer, default=5)  # 品相/履约
    efficiency_rating = db.Column(db.Integer, default=5)
    review_content = db.Column(db.Text)
    created_at = db.Column(db.String(50))

    __table_args__ = (
        db.UniqueConstraint('order_id', 'reviewer_id', name='unique_order_reviewer_review'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'order_id': self.order_id,
            'book_id': self.book_id or '',
            'reviewer_id': self.reviewer_id,
            'reviewer_name': self.reviewer_name or '',
            'reviewer_role': self.reviewer_role or '',
            'reviewed_user_id': self.reviewed_user_id or '',
            'description_rating': self.description_rating or self.service_rating or 0,
            'service_rating': self.service_rating or 0,
            'condition_rating': self.condition_rating or 0,
            'efficiency_rating': self.efficiency_rating or 0,
            'review_content': self.review_content or '',
            'created_at': self.created_at or ''
        }


class WantedPost(db.Model):
    """求购信息表"""
    __tablename__ = 'wanted_posts'

    id = db.Column(db.String(50), primary_key=True)
    user_id = db.Column(db.String(50), fk('users', 'CASCADE'), index=True, nullable=False)
    username = db.Column(db.String(100))
    title = db.Column(db.String(200), nullable=False, index=True)
    author = db.Column(db.String(100))
    isbn = db.Column(db.String(30), index=True)
    category = db.Column(db.String(50))
    max_price = db.Column(db.Float)
    desc = db.Column(db.Text)
    status = db.Column(db.String(20), default='open', index=True)  # open / closed
    created_at = db.Column(db.String(50))

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'username': self.username or '',
            'title': self.title,
            'author': self.author or '',
            'isbn': self.isbn or '',
            'category': self.category or 'other',
            'max_price': float(self.max_price) if self.max_price else None,
            'desc': self.desc or '',
            'status': self.status or 'open',
            'created_at': self.created_at or ''
        }


class Conversation(db.Model):
    """私信会话表"""
    __tablename__ = 'conversations'

    id = db.Column(db.String(50), primary_key=True)
    user_a_id = db.Column(db.String(50), fk('users', 'CASCADE'), index=True, nullable=False)
    user_b_id = db.Column(db.String(50), fk('users', 'CASCADE'), index=True, nullable=False)
    book_id = db.Column(db.String(50), default='')
    order_id = db.Column(db.String(50), default='')
    book_title = db.Column(db.String(200))
    last_preview = db.Column(db.String(300))
    updated_at = db.Column(db.String(50))
    created_at = db.Column(db.String(50))

    __table_args__ = (
        db.UniqueConstraint('user_a_id', 'user_b_id', 'book_id', 'order_id', name='unique_conversation_ctx'),
    )

    def peer_id_for(self, user_id):
        """返回会话中对方用户 id"""
        uid = str(user_id)
        return self.user_b_id if uid == self.user_a_id else self.user_a_id

    def to_dict(self, current_user_id=None):
        """含 peer_id（当前用户视角的对方 id）"""
        d = {
            'id': self.id,
            'user_a_id': self.user_a_id,
            'user_b_id': self.user_b_id,
            'book_id': self.book_id or '',
            'order_id': self.order_id or '',
            'book_title': self.book_title or '',
            'last_preview': self.last_preview or '',
            'updated_at': self.updated_at or '',
            'created_at': self.created_at or ''
        }
        if current_user_id:
            d['peer_id'] = self.peer_id_for(current_user_id)
        return d


class Message(db.Model):
    """私信消息表"""
    __tablename__ = 'messages'

    id = db.Column(db.String(50), primary_key=True)
    conversation_id = db.Column(db.String(50), fk('conversations', 'CASCADE'), index=True, nullable=False)
    sender_id = db.Column(db.String(50), fk('users', 'CASCADE'), index=True, nullable=False)
    sender_name = db.Column(db.String(100))
    msg_type = db.Column(db.String(20), default='text')  # text / image / audio / location / appointment / system
    content = db.Column(db.Text)
    media_url = db.Column(db.String(500))
    media_meta = db.Column(db.Text)
    appointment_id = db.Column(db.String(50))
    is_read = db.Column(db.Boolean, default=False, index=True)
    read_at = db.Column(db.String(50))
    is_recalled = db.Column(db.Boolean, default=False, index=True)
    recalled_at = db.Column(db.String(50))
    created_at = db.Column(db.String(50))

    def to_dict(self, appointment=None):
        """可选附带面约 appointment 详情"""
        meta = {}
        if self.media_meta:
            try:
                meta = json.loads(self.media_meta)
            except (json.JSONDecodeError, TypeError):
                meta = {}
        d = {
            'id': self.id,
            'conversation_id': self.conversation_id,
            'sender_id': self.sender_id,
            'sender_name': self.sender_name or '',
            'msg_type': self.msg_type or 'text',
            'content': self.content or '',
            'media_url': self.media_url or '',
            'media_meta': meta,
            'appointment_id': self.appointment_id or '',
            'is_read': bool(self.is_read),
            'read_at': self.read_at or '',
            'is_recalled': bool(self.is_recalled),
            'recalled_at': self.recalled_at or '',
            'created_at': self.created_at or ''
        }
        if appointment:
            d['appointment'] = appointment.to_dict()
        return d


class MeetingAppointment(db.Model):
    """面交预约表"""
    __tablename__ = 'meeting_appointments'

    id = db.Column(db.String(50), primary_key=True)
    conversation_id = db.Column(db.String(50), fk('conversations', 'CASCADE'), index=True, nullable=False)
    order_id = db.Column(db.String(50), default='')
    book_id = db.Column(db.String(50), default='')
    proposer_id = db.Column(db.String(50), fk('users', 'CASCADE'), index=True, nullable=False)
    place = db.Column(db.String(200), nullable=False)
    meeting_time = db.Column(db.String(50), nullable=False)
    note = db.Column(db.Text)
    status = db.Column(db.String(20), default='pending', index=True)  # pending / confirmed / cancelled
    created_at = db.Column(db.String(50))
    updated_at = db.Column(db.String(50))

    def to_dict(self):
        return {
            'id': self.id,
            'conversation_id': self.conversation_id,
            'order_id': self.order_id or '',
            'book_id': self.book_id or '',
            'proposer_id': self.proposer_id,
            'place': self.place,
            'meeting_time': self.meeting_time,
            'note': self.note or '',
            'status': self.status or 'pending',
            'created_at': self.created_at or '',
            'updated_at': self.updated_at or ''
        }


class PriceOffer(db.Model):
    """议价报价表"""
    __tablename__ = 'price_offers'

    id = db.Column(db.String(50), primary_key=True)
    book_id = db.Column(db.String(50), fk('books', 'CASCADE'), index=True, nullable=False)
    book_title = db.Column(db.String(200))
    buyer_id = db.Column(db.String(50), fk('users', 'CASCADE'), index=True, nullable=False)
    buyer_name = db.Column(db.String(100))
    seller_id = db.Column(db.String(50), fk('users', 'CASCADE'), index=True, nullable=False)
    offer_price = db.Column(db.Float, nullable=False)
    list_price = db.Column(db.Float)
    message = db.Column(db.Text)
    status = db.Column(db.String(20), default='pending', index=True)  # pending / accepted / rejected / cancelled
    created_at = db.Column(db.String(50))

    def to_dict(self):
        return {
            'id': self.id,
            'book_id': self.book_id,
            'book_title': self.book_title or '',
            'buyer_id': self.buyer_id,
            'buyer_name': self.buyer_name or '',
            'seller_id': self.seller_id,
            'offer_price': float(self.offer_price) if self.offer_price else 0,
            'list_price': float(self.list_price) if self.list_price else 0,
            'message': self.message or '',
            'status': self.status or 'pending',
            'created_at': self.created_at or ''
        }


class Notification(db.Model):
    """站内通知表"""
    __tablename__ = 'notifications'

    id = db.Column(db.String(50), primary_key=True)
    user_id = db.Column(db.String(50), fk('users', 'CASCADE'), index=True, nullable=False)
    ntype = db.Column(db.String(30), index=True)  # order / offer / audit / price_drop / new_book / review / appointment
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text)
    link = db.Column(db.String(300))
    is_read = db.Column(db.Boolean, default=False, index=True)
    created_at = db.Column(db.String(50))

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'ntype': self.ntype or '',
            'title': self.title,
            'content': self.content or '',
            'link': self.link or '',
            'is_read': bool(self.is_read),
            'created_at': self.created_at or ''
        }


class CampusSpot(db.Model):
    """校内面交点"""
    __tablename__ = 'campus_spots'

    id = db.Column(db.String(50), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    zone = db.Column(db.String(50), default='西校区')
    description = db.Column(db.String(300))
    sort_order = db.Column(db.Integer, default=0)
    map_x = db.Column(db.Float)
    map_y = db.Column(db.Float)
    created_at = db.Column(db.String(50))

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'zone': self.zone or '西校区',
            'description': self.description or '',
            'sort_order': self.sort_order or 0,
            'map_x': self.map_x,
            'map_y': self.map_y
        }


class CourseTextbook(db.Model):
    """课程-教材映射"""
    __tablename__ = 'course_textbooks'

    id = db.Column(db.String(50), primary_key=True)
    college = db.Column(db.String(100), index=True)
    major = db.Column(db.String(100), index=True)
    course_code = db.Column(db.String(50), index=True)
    course_name = db.Column(db.String(200))
    textbook_title = db.Column(db.String(200))
    textbook_author = db.Column(db.String(100))
    textbook_isbn = db.Column(db.String(30))
    created_at = db.Column(db.String(50))

    def to_dict(self):
        return {
            'id': self.id,
            'college': self.college,
            'major': self.major,
            'course_code': self.course_code,
            'course_name': self.course_name,
            'textbook_title': self.textbook_title,
            'textbook_author': self.textbook_author or '',
            'textbook_isbn': self.textbook_isbn or ''
        }


class SemesterCampaign(db.Model):
    """学期主题活动"""
    __tablename__ = 'semester_campaigns'

    id = db.Column(db.String(50), primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    campaign_type = db.Column(db.String(30))  # back_to_school / clearance
    tag = db.Column(db.String(50), index=True)
    start_date = db.Column(db.String(20))
    end_date = db.Column(db.String(20))
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True, index=True)
    created_at = db.Column(db.String(50))

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'campaign_type': self.campaign_type or '',
            'tag': self.tag or '',
            'start_date': self.start_date or '',
            'end_date': self.end_date or '',
            'description': self.description or '',
            'is_active': bool(self.is_active)
        }


class NotificationOutbox(db.Model):
    """邮件/短信推送记录（模拟通道，便于审计）"""
    __tablename__ = 'notification_outbox'

    id = db.Column(db.String(50), primary_key=True)
    user_id = db.Column(db.String(50), fk('users', 'CASCADE'), index=True, nullable=False)
    channel = db.Column(db.String(20), index=True)  # email / sms
    recipient = db.Column(db.String(200))
    title = db.Column(db.String(200))
    content = db.Column(db.Text)
    status = db.Column(db.String(20), default='sent')  # sent / failed
    created_at = db.Column(db.String(50))

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'channel': self.channel,
            'recipient': self.recipient or '',
            'title': self.title or '',
            'content': self.content or '',
            'status': self.status or 'sent',
            'created_at': self.created_at or ''
        }


class CampusSchool(db.Model):
    """多校配置"""
    __tablename__ = 'campus_schools'

    id = db.Column(db.String(50), primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    email_domains = db.Column(db.Text)  # JSON 数组，如 ["edu.cn","stu.xxx.edu.cn"]
    is_active = db.Column(db.Boolean, default=True, index=True)
    sort_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.String(50))

    def domain_list(self):
        """解析 email_domains JSON → 学籍认证后缀列表"""
        if not self.email_domains:
            return []
        try:
            return json.loads(self.email_domains) if isinstance(self.email_domains, str) else self.email_domains
        except Exception:
            return []

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email_domains': self.domain_list(),
            'is_active': bool(self.is_active),
            'sort_order': self.sort_order or 0,
            'created_at': self.created_at or ''
        }


class UserBlock(db.Model):
    """用户拉黑"""
    __tablename__ = 'user_blocks'

    id = db.Column(db.String(50), primary_key=True)
    blocker_id = db.Column(db.String(50), fk('users', 'CASCADE'), index=True, nullable=False)
    blocked_id = db.Column(db.String(50), fk('users', 'CASCADE'), index=True, nullable=False)
    created_at = db.Column(db.String(50))

    __table_args__ = (db.UniqueConstraint('blocker_id', 'blocked_id', name='unique_user_block'),)

    def to_dict(self):
        return {
            'id': self.id,
            'blocker_id': self.blocker_id,
            'blocked_id': self.blocked_id,
            'created_at': self.created_at or ''
        }


class Report(db.Model):
    """举报"""
    __tablename__ = 'reports'

    id = db.Column(db.String(50), primary_key=True)
    reporter_id = db.Column(db.String(50), fk('users', 'CASCADE'), index=True, nullable=False)
    reporter_name = db.Column(db.String(100))
    target_type = db.Column(db.String(30), index=True)  # user / book / comment
    target_id = db.Column(db.String(50), index=True, nullable=False)
    reason = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='pending', index=True)  # pending / handled / dismissed
    admin_note = db.Column(db.Text)
    created_at = db.Column(db.String(50))

    def to_dict(self):
        return {
            'id': self.id,
            'reporter_id': self.reporter_id,
            'reporter_name': self.reporter_name or '',
            'target_type': self.target_type,
            'target_id': self.target_id,
            'reason': self.reason or '',
            'status': self.status or 'pending',
            'admin_note': self.admin_note or '',
            'created_at': self.created_at or ''
        }


class SensitiveWord(db.Model):
    """敏感词"""
    __tablename__ = 'sensitive_words'

    id = db.Column(db.String(50), primary_key=True)
    word = db.Column(db.String(100), nullable=False, index=True)
    scope = db.Column(db.String(20), default='all')  # all / comment / message
    is_active = db.Column(db.Boolean, default=True, index=True)
    created_at = db.Column(db.String(50))

    def to_dict(self):
        return {
            'id': self.id,
            'word': self.word,
            'scope': self.scope or 'all',
            'is_active': bool(self.is_active),
            'created_at': self.created_at or ''
        }


class AdminAuditLog(db.Model):
    """管理员操作日志"""
    __tablename__ = 'admin_audit_logs'

    id = db.Column(db.String(50), primary_key=True)
    admin_id = db.Column(db.String(50), fk('users', 'RESTRICT'), index=True, nullable=False)
    admin_name = db.Column(db.String(100))
    action = db.Column(db.String(80), index=True)
    target_type = db.Column(db.String(40))
    target_id = db.Column(db.String(50))
    detail = db.Column(db.Text)
    ip = db.Column(db.String(50))
    created_at = db.Column(db.String(50))

    def to_dict(self):
        return {
            'id': self.id,
            'admin_id': self.admin_id,
            'admin_name': self.admin_name or '',
            'action': self.action or '',
            'target_type': self.target_type or '',
            'target_id': self.target_id or '',
            'detail': self.detail or '',
            'ip': self.ip or '',
            'created_at': self.created_at or ''
        }


class IsbnBlacklist(db.Model):
    """违禁/盗版 ISBN 黑名单"""
    __tablename__ = 'isbn_blacklist'

    id = db.Column(db.String(50), primary_key=True)
    isbn = db.Column(db.String(30), unique=True, nullable=False, index=True)
    reason = db.Column(db.Text)
    created_at = db.Column(db.String(50))

    def to_dict(self):
        return {
            'id': self.id,
            'isbn': self.isbn,
            'reason': self.reason or '',
            'created_at': self.created_at or ''
        }


class BanAppeal(db.Model):
    """封禁申诉"""
    __tablename__ = 'ban_appeals'

    id = db.Column(db.String(50), primary_key=True)
    user_id = db.Column(db.String(50), fk('users', 'CASCADE'), index=True, nullable=False)
    username = db.Column(db.String(100))
    ban_level = db.Column(db.String(20))
    content = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='pending', index=True)  # pending / approved / rejected
    admin_reply = db.Column(db.Text)
    handled_by = db.Column(db.String(50), fk('users'))
    created_at = db.Column(db.String(50))
    updated_at = db.Column(db.String(50))

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'username': self.username or '',
            'ban_level': self.ban_level or '',
            'content': self.content or '',
            'status': self.status or 'pending',
            'admin_reply': self.admin_reply or '',
            'handled_by': self.handled_by or '',
            'created_at': self.created_at or '',
            'updated_at': self.updated_at or ''
        }


class BookView(db.Model):
    """书籍浏览记录：个性化推荐 + seller 浏览量"""
    __tablename__ = 'book_views'

    id = db.Column(db.String(50), primary_key=True)
    book_id = db.Column(db.String(50), fk('books', 'CASCADE'), index=True, nullable=False)
    user_id = db.Column(db.String(50), fk('users'), index=True, default='')
    created_at = db.Column(db.String(50))


class PublishTemplate(db.Model):
    """用户发布模板：payload 存 JSON 草稿"""
    __tablename__ = 'publish_templates'

    id = db.Column(db.String(50), primary_key=True)
    user_id = db.Column(db.String(50), fk('users', 'CASCADE'), index=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    payload = db.Column(db.Text)
    created_at = db.Column(db.String(50))

    def to_dict(self):
        payload = {}
        if self.payload:
            try:
                payload = json.loads(self.payload)
            except (json.JSONDecodeError, TypeError):
                payload = {}
        return {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'payload': payload,
            'created_at': self.created_at or ''
        }


class UserFollow(db.Model):
    """关注卖家：上新 push_notification"""
    __tablename__ = 'user_follows'

    id = db.Column(db.String(50), primary_key=True)
    follower_id = db.Column(db.String(50), fk('users', 'CASCADE'), index=True, nullable=False)
    seller_id = db.Column(db.String(50), fk('users', 'CASCADE'), index=True, nullable=False)
    created_at = db.Column(db.String(50))

    __table_args__ = (
        db.UniqueConstraint('follower_id', 'seller_id', name='unique_user_follow'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'follower_id': self.follower_id,
            'seller_id': self.seller_id,
            'created_at': self.created_at or ''
        }


class Setting(db.Model):
    """系统设置 KV 表：admin 配置、ISBN Key、SMS webhook 等"""
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

