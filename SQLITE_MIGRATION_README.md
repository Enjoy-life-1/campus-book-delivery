# SQLite 数据库迁移说明

本项目已从 JSON 文件存储迁移到 SQLite 数据库。

## 文件说明

1. **models.py** - 数据库模型定义，包含所有表结构：
   - User (用户表)
   - Book (书籍表)
   - Order (订单表)
   - Collection (收藏表)
   - CartItem (购物车表)
   - Setting (系统设置表)

2. **init_db.py** - 数据库初始化脚本，用于创建数据库表和默认数据

3. **migrate_json_to_sqlite.py** - 数据迁移脚本，将现有 JSON 数据导入 SQLite

4. **app.py** - 主应用文件，已更新为使用 SQLite 数据库

## 使用步骤

### 方式一：一键运行脚本（推荐）

#### Windows 用户：
双击运行 `setup_and_run.bat` 或在命令行执行：
```bash
setup_and_run.bat
```

#### Linux/Mac 用户：
```bash
chmod +x setup_and_run.sh
./setup_and_run.sh
```

#### 跨平台 Python 脚本：
```bash
python setup_and_run.py
```

这些脚本会自动完成：
1. 检查并安装依赖
2. 初始化数据库
3. 检测并迁移现有 JSON 数据（可选）
4. 启动应用

### 方式二：手动步骤

#### 1. 安装依赖

```bash
pip install -r requirements.txt
```

#### 2. 初始化数据库

首次运行或需要重新创建数据库时：

```bash
python init_db.py
```

这将创建 `campus_book_delivery.db` 数据库文件，并创建默认的管理员账户：
- 用户名: `admin`
- 密码: `admin123`

#### 3. 迁移现有数据（可选）

如果你有现有的 JSON 数据需要迁移到 SQLite：

```bash
python migrate_json_to_sqlite.py
```

这将读取 `database/` 目录下的 JSON 文件，并将数据导入到 SQLite 数据库中。

#### 4. 运行应用

```bash
python app.py
```

或

```bash
python run.py
```

## 数据库文件

数据库文件 `campus_book_delivery.db` 将保存在项目根目录下。

## 注意事项

1. **备份数据**：在迁移前，建议备份 `database/` 目录下的 JSON 文件

2. **数据迁移**：迁移脚本会自动跳过已存在的数据，可以安全地多次运行

3. **JSON 文件**：迁移后，原有的 JSON 文件仍然保留，但应用不再使用它们。你可以选择删除或保留作为备份

4. **数据库位置**：数据库文件位于项目根目录，名为 `campus_book_delivery.db`

## 数据库结构

### users 表
- id (主键)
- username (唯一)
- password
- email
- phone
- school
- introduction
- avatar
- is_admin
- created_at
- updated_at

### books 表
- id (主键)
- title
- author
- category
- price
- desc
- imgs (JSON 字符串)
- contact
- stock
- status
- owner_id
- owner_name
- seller
- created_at
- updated_at

### orders 表
- id (主键)
- book_id
- book_title
- buyer_id
- buyer_name
- seller_id
- seller_name
- price
- status
- created_at

### collections 表
- id (主键)
- book_id
- user_id
- username
- created_at
- 唯一约束: (book_id, user_id)

### cart 表
- id (主键)
- user_id
- book_id
- quantity
- created_at
- updated_at

### settings 表
- id (主键，自增)
- key (唯一)
- value
- updated_at

## 查看数据库数据

### 方法一：使用 Python 脚本（推荐）

#### 交互式查看（详细）
```bash
python view_database.py
```
提供菜单选择，可以查看：
- 用户数据
- 书籍数据
- 订单数据
- 收藏数据
- 购物车数据
- 系统设置
- 统计信息

#### 快速查看（概览）
```bash
python view_database_simple.py
```
快速显示数据库概览和统计信息

### 方法二：使用 SQLite 命令行工具

```bash
# 进入 SQLite 命令行
sqlite3 campus_book_delivery.db

# 查看所有表
.tables

# 查看用户表数据
SELECT * FROM users;

# 查看书籍表数据
SELECT * FROM books;

# 查看订单表数据
SELECT * FROM orders;

# 退出
.quit
```

### 方法三：使用图形化工具

推荐使用 **DB Browser for SQLite**（免费）：
1. 下载安装：https://sqlitebrowser.org/
2. 打开 `campus_book_delivery.db` 文件
3. 在图形界面中浏览和编辑数据

### 方法四：在 Python 中直接查询

```python
from app import app
from models import db, User, Book, Order

with app.app_context():
    # 查看所有用户
    users = User.query.all()
    for user in users:
        print(user.username)
    
    # 查看所有书籍
    books = Book.query.all()
    for book in books:
        print(book.title)
```

## 故障排除

如果遇到问题：

1. 删除 `campus_book_delivery.db` 文件，然后重新运行 `init_db.py`
2. 检查是否有足够的文件系统权限
3. 确保已安装所有依赖：`pip install -r requirements.txt`

