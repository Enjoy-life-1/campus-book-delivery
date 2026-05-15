"""
数据迁移脚本
将现有的 JSON 文件数据迁移到 SQLite 数据库
"""
from flask import Flask
from models import db, User, Book, Order, Collection, CartItem, Setting
import json
import os
import time

# 创建 Flask 应用实例
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///campus_book_delivery.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# JSON 文件路径
DB_DIR = 'database'
USERS_DB = os.path.join(DB_DIR, 'users.json')
BOOKS_DB = os.path.join(DB_DIR, 'books.json')
ORDERS_DB = os.path.join(DB_DIR, 'orders.json')
COLLECTIONS_DB = os.path.join(DB_DIR, 'collections.json')
CART_DB = os.path.join(DB_DIR, 'cart.json')
SETTINGS_DB = os.path.join(DB_DIR, 'settings.json')

def read_json_file(file_path):
    """读取 JSON 文件"""
    if not os.path.exists(file_path):
        return [] if 'settings' not in file_path else {}
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError:
        return [] if 'settings' not in file_path else {}

def migrate_users():
    """迁移用户数据"""
    print("开始迁移用户数据...")
    users_data = read_json_file(USERS_DB)
    if not users_data:
        print("  没有用户数据需要迁移")
        return
    
    migrated = 0
    for user_data in users_data:
        # 检查用户是否已存在
        existing_user = User.query.filter_by(id=str(user_data.get('id', ''))).first()
        if existing_user:
            print(f"  用户 {user_data.get('username')} 已存在，跳过")
            continue
        
        user = User(
            id=str(user_data.get('id', '')),
            username=user_data.get('username', ''),
            password=user_data.get('password', ''),
            email=user_data.get('email', ''),
            phone=user_data.get('phone', ''),
            school=user_data.get('school', ''),
            introduction=user_data.get('introduction', ''),
            avatar=user_data.get('avatar', ''),
            is_admin=user_data.get('is_admin', False),
            created_at=user_data.get('created_at', ''),
            updated_at=user_data.get('updated_at', '')
        )
        db.session.add(user)
        migrated += 1
    
    db.session.commit()
    print(f"  成功迁移 {migrated} 个用户")

def migrate_books():
    """迁移书籍数据"""
    print("开始迁移书籍数据...")
    books_data = read_json_file(BOOKS_DB)
    if not books_data:
        print("  没有书籍数据需要迁移")
        return
    
    migrated = 0
    updated = 0
    for book_data in books_data:
        # 检查书籍是否已存在
        existing_book = Book.query.filter_by(id=str(book_data.get('id', ''))).first()
        if existing_book:
            # 如果书籍已存在，检查是否需要更新 description
            description = book_data.get('description', '') or book_data.get('desc', '')
            if description and existing_book.description != description:
                existing_book.description = description
                existing_book.desc = description
                updated += 1
                print(f"  更新书籍 {book_data.get('title')} 的简介")
            else:
                print(f"  书籍 {book_data.get('title')} 已存在，跳过")
            continue
        
        # 处理图片数组
        imgs = book_data.get('imgs', [])
        if isinstance(imgs, str):
            imgs = [imgs]
        imgs_json = json.dumps(imgs, ensure_ascii=False) if imgs else ''
        
        book = Book(
            id=str(book_data.get('id', '')),
            title=book_data.get('title', ''),
            author=book_data.get('author', ''),
            category=book_data.get('category', 'other'),
            price=float(book_data.get('price', 0)),
            desc=book_data.get('desc', '') or book_data.get('description', ''),
            description=book_data.get('description', '') or book_data.get('desc', ''),
            imgs=imgs_json,
            image=book_data.get('image', '') or (imgs[0] if imgs else ''),
            cover_url=book_data.get('cover_url', '') or (imgs[0] if imgs else ''),
            contact=book_data.get('contact', ''),
            stock=int(book_data.get('stock', 1)),
            status=book_data.get('status', 'available'),
            owner_id=str(book_data.get('owner_id', '')) if book_data.get('owner_id') else '',
            owner_name=book_data.get('owner_name', ''),
            seller=book_data.get('seller', ''),
            sellerId=str(book_data.get('sellerId', '')) if book_data.get('sellerId') else '',
            createTime=book_data.get('createTime', ''),
            created_at=book_data.get('created_at', ''),
            updated_at=book_data.get('updated_at', ''),
            publish_date=book_data.get('publish_date', '')
        )
        db.session.add(book)
        migrated += 1
    
    db.session.commit()
    print(f"  成功迁移 {migrated} 本书籍")
    if updated > 0:
        print(f"  成功更新 {updated} 本书籍的简介")

def migrate_orders():
    """迁移订单数据"""
    print("开始迁移订单数据...")
    orders_data = read_json_file(ORDERS_DB)
    if not orders_data:
        print("  没有订单数据需要迁移")
        return
    
    migrated = 0
    for order_data in orders_data:
        # 检查订单是否已存在
        existing_order = Order.query.filter_by(id=str(order_data.get('id', ''))).first()
        if existing_order:
            print(f"  订单 {order_data.get('id')} 已存在，跳过")
            continue
        
        order = Order(
            id=str(order_data.get('id', '')),
            book_id=str(order_data.get('book_id', '')),
            book_title=order_data.get('book_title', ''),
            buyer_id=str(order_data.get('buyer_id', '')),
            buyer_name=order_data.get('buyer_name', ''),
            seller_id=str(order_data.get('seller_id', '')),
            seller_name=order_data.get('seller_name', ''),
            price=float(order_data.get('price', 0)),
            status=order_data.get('status', 'pending'),
            created_at=order_data.get('created_at', '')
        )
        db.session.add(order)
        migrated += 1
    
    db.session.commit()
    print(f"  成功迁移 {migrated} 个订单")

def migrate_collections():
    """迁移收藏数据"""
    print("开始迁移收藏数据...")
    collections_data = read_json_file(COLLECTIONS_DB)
    if not collections_data:
        print("  没有收藏数据需要迁移")
        return
    
    migrated = 0
    skipped = 0
    for collection_data in collections_data:
        # 检查收藏是否已存在（基于 book_id 和 user_id 的唯一约束）
        existing = Collection.query.filter_by(
            book_id=str(collection_data.get('book_id', '')),
            user_id=str(collection_data.get('user_id', ''))
        ).first()
        if existing:
            skipped += 1
            continue
        
        collection = Collection(
            id=str(collection_data.get('id', '')),
            book_id=str(collection_data.get('book_id', '')),
            user_id=str(collection_data.get('user_id', '')),
            username=collection_data.get('username', ''),
            created_at=collection_data.get('created_at', '')
        )
        db.session.add(collection)
        migrated += 1
    
    db.session.commit()
    print(f"  成功迁移 {migrated} 个收藏，跳过 {skipped} 个重复项")

def migrate_cart():
    """迁移购物车数据"""
    print("开始迁移购物车数据...")
    cart_data = read_json_file(CART_DB)
    if not cart_data:
        print("  没有购物车数据需要迁移")
        return
    
    migrated = 0
    for cart_item_data in cart_data:
        # 检查购物车项是否已存在
        existing = CartItem.query.filter_by(id=str(cart_item_data.get('id', ''))).first()
        if existing:
            print(f"  购物车项 {cart_item_data.get('id')} 已存在，跳过")
            continue
        
        cart_item = CartItem(
            id=str(cart_item_data.get('id', '')),
            user_id=str(cart_item_data.get('user_id', '')),
            book_id=str(cart_item_data.get('book_id', '')),
            quantity=int(cart_item_data.get('quantity', 1)),
            created_at=cart_item_data.get('created_at', ''),
            updated_at=cart_item_data.get('updated_at', '')
        )
        db.session.add(cart_item)
        migrated += 1
    
    db.session.commit()
    print(f"  成功迁移 {migrated} 个购物车项")

def migrate_settings():
    """迁移系统设置数据"""
    print("开始迁移系统设置数据...")
    settings_data = read_json_file(SETTINGS_DB)
    if not settings_data or not isinstance(settings_data, dict):
        print("  没有系统设置数据需要迁移")
        return
    
    migrated = 0
    for key, value in settings_data.items():
        if key == 'updated_at':
            continue
        
        # 检查设置是否已存在
        existing = Setting.query.filter_by(key=key).first()
        if existing:
            # 更新现有设置
            if isinstance(value, (dict, list)):
                existing.value = json.dumps(value, ensure_ascii=False)
            elif isinstance(value, bool):
                existing.value = str(value).lower()
            else:
                existing.value = str(value)
            existing.updated_at = settings_data.get('updated_at', time.strftime('%Y-%m-%d %H:%M:%S'))
        else:
            # 创建新设置
            if isinstance(value, (dict, list)):
                value_str = json.dumps(value, ensure_ascii=False)
            elif isinstance(value, bool):
                value_str = str(value).lower()
            else:
                value_str = str(value)
            
            setting = Setting(
                key=key,
                value=value_str,
                updated_at=settings_data.get('updated_at', time.strftime('%Y-%m-%d %H:%M:%S'))
            )
            db.session.add(setting)
        migrated += 1
    
    db.session.commit()
    print(f"  成功迁移 {migrated} 个系统设置")

def main():
    """主函数"""
    print("=" * 50)
    print("开始数据迁移...")
    print("=" * 50)
    
    with app.app_context():
        # 确保数据库表已创建
        db.create_all()
        print("数据库表已就绪\n")
        
        # 迁移各个表的数据
        migrate_users()
        print()
        migrate_books()
        print()
        migrate_orders()
        print()
        migrate_collections()
        print()
        migrate_cart()
        print()
        migrate_settings()
        print()
        
        print("=" * 50)
        print("数据迁移完成！")
        print("=" * 50)

if __name__ == '__main__':
    main()

