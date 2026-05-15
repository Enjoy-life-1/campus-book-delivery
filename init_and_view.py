
"""
自动初始化数据库并查看数据
"""
import os
import sys

def main():
    print("\n" + "=" * 70)
    print("  自动初始化数据库并查看")
    print("=" * 70)
    
    # 检查数据库文件位置（可能在根目录或instance文件夹）
    db_file_root = 'campus_book_delivery.db'
    db_file_instance = os.path.join('instance', 'campus_book_delivery.db')
    
    db_file = None
    if os.path.exists(db_file_instance):
        db_file = db_file_instance
        print(f"\n✓ 找到数据库文件: {db_file_instance}")
    elif os.path.exists(db_file_root):
        db_file = db_file_root
        print(f"\n✓ 找到数据库文件: {db_file_root}")
    
    # 如果数据库不存在，则初始化
    if db_file is None:
        print("\n检测到数据库不存在，正在初始化...")
        try:
            from init_db import init_database
            init_database()
            print("✓ 数据库初始化完成！")
            # 重新检查数据库位置
            if os.path.exists(db_file_instance):
                db_file = db_file_instance
            elif os.path.exists(db_file_root):
                db_file = db_file_root
        except Exception as e:
            print(f"✗ 初始化失败: {e}")
            import traceback
            traceback.print_exc()
            print("\n请手动运行: python init_db.py")
            return
    
    # 查看数据库
    print("\n正在加载数据库内容...\n")
    try:
        from view_database_simple import main as view_main
        view_main()
    except Exception as e:
        print(f"✗ 查看数据库失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()

