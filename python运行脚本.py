"""
一键设置和运行脚本
自动初始化数据库、迁移数据并启动应用
"""
import os
import sys
import subprocess

def print_step(step_num, description):
    """打印步骤信息"""
    print("\n" + "=" * 60)
    print(f"步骤 {step_num}: {description}")
    print("=" * 60)

def check_dependencies():
    """检查依赖是否已安装"""
    print_step(1, "检查依赖")
    try:
        import flask
        import flask_sqlalchemy
        import flask_cors
        print("✓ 所有依赖已安装")
        return True
    except ImportError as e:
        print(f"✗ 缺少依赖: {e}")
        print("\n正在安装依赖...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
            print("✓ 依赖安装完成")
            return True
        except subprocess.CalledProcessError:
            print("✗ 依赖安装失败，请手动运行: pip install -r requirements.txt")
            return False

def init_database():
    """初始化数据库"""
    print_step(2, "初始化数据库")
    try:
        from init_db import init_database
        init_database()
        print("✓ 数据库初始化完成")
        return True
    except Exception as e:
        print(f"✗ 数据库初始化失败: {e}")
        return False

def migrate_data():
    """迁移数据"""
    print_step(3, "迁移现有数据")
    
    # 检查是否有 JSON 文件
    json_files = [
        'database/users.json',
        'database/books.json',
        'database/orders.json',
        'database/collections.json',
        'database/cart.json',
        'database/settings.json'
    ]
    
    has_json_data = any(os.path.exists(f) for f in json_files)
    
    if not has_json_data:
        print("ℹ 未找到 JSON 数据文件，跳过数据迁移")
        return True
    
    response = input("\n检测到 JSON 数据文件，是否要迁移到 SQLite？(y/n，默认 y): ").strip().lower()
    if response and response != 'y':
        print("ℹ 跳过数据迁移")
        return True
    
    try:
        from migrate_json_to_sqlite import main
        main()
        print("✓ 数据迁移完成")
        return True
    except Exception as e:
        print(f"✗ 数据迁移失败: {e}")
        print("ℹ 你可以稍后手动运行: python migrate_json_to_sqlite.py")
        return True  # 迁移失败不影响运行

def run_app():
    """运行应用"""
    print_step(4, "启动应用")
    print("\n应用将在 http://localhost:5000 启动")
    print("按 Ctrl+C 停止应用\n")
    
    try:
        # 检查是否有 run.py，如果有则使用它
        if os.path.exists('run.py'):
            subprocess.call([sys.executable, "run.py"])
        else:
            subprocess.call([sys.executable, "app.py"])
    except KeyboardInterrupt:
        print("\n\n应用已停止")
    except Exception as e:
        print(f"\n✗ 启动应用失败: {e}")

def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("校园书递项目 - SQLite 数据库设置和运行")
    print("=" * 60)
    
    # 检查依赖
    if not check_dependencies():
        print("\n✗ 请先安装依赖后再运行")
        return
    
    # 初始化数据库
    if not init_database():
        print("\n✗ 数据库初始化失败，请检查错误信息")
        return
    
    # 迁移数据
    migrate_data()
    
    # 运行应用
    run_app()

if __name__ == '__main__':
    main()

