"""
简单查看数据库 - 快速显示所有数据
"""
from flask import Flask
from models import db, User, Book, Order, Collection, CartItem, Setting
import os

def get_database_uri():
    """检测数据库文件位置并返回相应的URI"""
    db_file_root = 'campus_book_delivery.db'
    db_file_instance = os.path.join('instance', 'campus_book_delivery.db')
    
    if os.path.exists(db_file_instance):
        # instance文件夹中的数据库，使用绝对路径
        abs_path = os.path.abspath(db_file_instance)
        # Windows路径需要转换为正斜杠
        uri_path = abs_path.replace('\\', '/')
        # SQLite URI格式: sqlite:///absolute/path
        return f'sqlite:///{uri_path}', db_file_instance
    elif os.path.exists(db_file_root):
        # 根目录的数据库，使用绝对路径
        abs_path = os.path.abspath(db_file_root)
        uri_path = abs_path.replace('\\', '/')
        return f'sqlite:///{uri_path}', db_file_root
    else:
        # 默认使用根目录路径（如果数据库不存在）
        return 'sqlite:///campus_book_delivery.db', None

def create_app(db_uri):
    """创建Flask应用实例"""
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    return app

def main():
    # 检查数据库文件是否存在
    db_uri, db_file = get_database_uri()
    
    if db_file is None:
        print(f"✗ 数据库文件不存在")
        print(f"  检查路径: campus_book_delivery.db")
        print(f"  检查路径: instance/campus_book_delivery.db")
        print("\n" + "=" * 70)
        print("  提示：需要先初始化数据库")
        print("=" * 70)
        print("\n请运行以下命令之一来初始化数据库：")
        print("  1. python init_db.py")
        print("  2. 运行 查看数据库.bat（会自动初始化）")
        print("\n或者直接运行以下命令自动初始化并查看：")
        print("  python -c \"from init_db import init_database; init_database()\"")
        
        # 询问是否自动初始化
        try:
            response = input("\n是否现在自动初始化数据库？(y/n，默认 y): ").strip().lower()
            if not response or response == 'y':
                print("\n正在初始化数据库...")
                from init_db import init_database
                init_database()
                print("✓ 数据库初始化完成！\n")
                # 重新检查数据库位置
                db_uri, db_file = get_database_uri()
                if not db_file:
                    print("✗ 初始化后仍未找到数据库文件")
                    return
            else:
                return
        except Exception as e:
            print(f"\n✗ 初始化失败: {e}")
            import traceback
            traceback.print_exc()
            print("\n请手动运行: python init_db.py")
            return
    
    print(f"✓ 找到数据库文件: {db_file}\n")
    
    # 创建Flask应用
    app = create_app(db_uri)
    
    with app.app_context():
        print("\n" + "=" * 70)
        print("  数据库概览")
        print("=" * 70)
        
        # 统计信息
        print(f"\n📊 统计信息:")
        print(f"  用户: {User.query.count()} 个")
        print(f"  书籍: {Book.query.count()} 本")
        print(f"  订单: {Order.query.count()} 个")
        print(f"  收藏: {Collection.query.count()} 个")
        print(f"  购物车: {CartItem.query.count()} 项")
        
        # 用户列表
        print(f"\n👥 用户列表 (前10个):")
        users = User.query.limit(10).all()
        for user in users:
            admin_tag = " [管理员]" if user.is_admin else ""
            print(f"  - {user.username} (ID: {user.id}){admin_tag}")
        if User.query.count() > 10:
            print(f"  ... 还有 {User.query.count() - 10} 个用户")
        
        # 书籍列表
        print(f"\n📚 书籍列表 (前10本):")
        books = Book.query.limit(10).all()
        for book in books:
            status_tag = " [已售]" if book.status == 'sold' else ""
            print(f"  - {book.title} - ¥{book.price:.2f} (ID: {book.id}){status_tag}")
        if Book.query.count() > 10:
            print(f"  ... 还有 {Book.query.count() - 10} 本书")
        
        # 订单列表
        print(f"\n📦 订单列表 (前10个):")
        orders = Order.query.limit(10).all()
        for order in orders:
            print(f"  - {order.book_title} - {order.buyer_name} → {order.seller_name} [{order.status}]")
        if Order.query.count() > 10:
            print(f"  ... 还有 {Order.query.count() - 10} 个订单")
        
        print("\n" + "=" * 70)
        print("  数据库查看完成")
        print("=" * 70 + "\n")

if __name__ == '__main__':
    main()

