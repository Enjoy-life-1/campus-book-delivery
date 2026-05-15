"""
更新书籍简介脚本
从 books.json 读取 description 字段并更新到数据库
"""
from flask import Flask
from models import db, Book
import json
import os

# 创建 Flask 应用实例
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///campus_book_delivery.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# JSON 文件路径
DB_DIR = 'database'
BOOKS_DB = os.path.join(DB_DIR, 'books.json')

def read_json_file(file_path):
    """读取 JSON 文件"""
    if not os.path.exists(file_path):
        return []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError:
        return []

def update_book_descriptions():
    """更新书籍简介"""
    print("开始更新书籍简介...")
    books_data = read_json_file(BOOKS_DB)
    if not books_data:
        print("  没有书籍数据")
        return
    
    updated = 0
    for book_data in books_data:
        book_id = str(book_data.get('id', ''))
        if not book_id:
            continue
        
        # 查找数据库中的书籍
        existing_book = Book.query.filter_by(id=book_id).first()
        if not existing_book:
            print(f"  书籍 ID {book_id} ({book_data.get('title')}) 在数据库中不存在，跳过")
            continue
        
        # 获取 description 字段
        description = book_data.get('description', '') or book_data.get('desc', '')
        
        # 如果 JSON 中有 description 且与数据库中的不同，则更新
        if description and existing_book.description != description:
            existing_book.description = description
            existing_book.desc = description  # 同时更新 desc 字段以保持兼容
            updated += 1
            print(f"  更新书籍 ID {book_id} ({book_data.get('title')}) 的简介")
    
    if updated > 0:
        db.session.commit()
        print(f"  成功更新 {updated} 本书籍的简介")
    else:
        print("  没有需要更新的书籍")

def main():
    """主函数"""
    print("=" * 50)
    print("开始更新书籍简介...")
    print("=" * 50)
    
    with app.app_context():
        update_book_descriptions()
        print()
        print("=" * 50)
        print("更新完成！")
        print("=" * 50)

if __name__ == '__main__':
    main()





