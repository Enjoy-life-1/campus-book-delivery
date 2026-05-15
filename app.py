from flask import Flask, request, jsonify, render_template, session, redirect, url_for
from flask_cors import CORS
import json
import os
import time
import hashlib
import re
from collections import Counter
from models import db, User, Book, Order, Collection, CartItem, Setting

app = Flask(__name__, 
            static_folder='static',
            template_folder='templates')
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///campus_book_delivery.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
CORS(app, supports_credentials=True)

# 初始化数据库
db.init_app(app)

# 添加安全响应头
@app.after_request
def add_security_headers(response):
    # 防止MIME类型嗅探
    response.headers['X-Content-Type-Options'] = 'nosniff'
    return response

# 为静态文件添加缓存控制和immutable指令
@app.route('/static/<path:filename>')
def static_cached(filename):
    # 获取原始静态文件响应
    response = app.send_static_file(filename)
    # 检查是否是CSS或JavaScript文件，这些文件通常应该使用缓存破坏
    if filename.endswith(('.css', '.js', '.jpg', '.jpeg', '.png', '.gif')):
        # 添加缓存控制头，设置为1年并使用immutable指令
        response.headers['Cache-Control'] = 'max-age=31536000, immutable'
    return response

# 数据库文件路径（保留用于向后兼容，但不再使用）
DB_DIR = 'database'
USERS_JSON = os.path.join(DB_DIR, 'users.json')

# 同步用户数据到 JSON 文件
def sync_users_to_json():
    """将数据库中的用户数据同步到 users.json 文件"""
    try:
        users = User.query.all()
        users_data = []
        for user in users:
            user_dict = {
                'id': user.id,
                'username': user.username,
                'password': user.password,
                'email': user.email or '',
                'phone': user.phone or '',
                'school': user.school or '',
                'introduction': user.introduction or '',
                'avatar': user.avatar or '',
                'is_admin': user.is_admin,
                'created_at': user.created_at or '',
                'updated_at': user.updated_at or ''
            }
            users_data.append(user_dict)
        
        # 确保 database 目录存在
        os.makedirs(DB_DIR, exist_ok=True)
        
        # 写入 JSON 文件
        with open(USERS_JSON, 'w', encoding='utf-8') as f:
            json.dump(users_data, f, ensure_ascii=False, indent=4)
        
        return True
    except Exception as e:
        print(f'同步用户数据到 JSON 文件失败: {e}')
        return False

# 工具函数：获取月销量
def get_monthly_sales_value(orders=None):
    if orders is None:
        orders = [order.to_dict() for order in Order.query.all()]
    current_month_prefix = time.strftime('%Y-%m')
    return sum(
        1 for order in orders
        if order.get('created_at', '').startswith(current_month_prefix)
    )

# 工具函数：获取待处理数量
def get_pending_reviews_value(orders=None):
    if orders is None:
        return Order.query.filter_by(status='pending').count()
    return sum(1 for order in orders if order.get('status') == 'pending')

# 工具函数：生成唯一ID
def generate_id():
    return str(int(time.time() * 1000))

# 工具函数：密码哈希
def hash_password(password):
    return hashlib.md5(password.encode()).hexdigest()

# 检查用户是否已登录
def is_logged_in():
    return 'user_id' in session

# 检查用户是否为管理员
def is_admin():
    if not is_logged_in():
        return False
    user = User.query.filter_by(id=str(session['user_id'])).first()
    return user.is_admin if user else False

# 首页路由 - 支持Vue SPA
@app.route('/')
def index():
    # 如果Vue构建文件存在，返回Vue应用
    vue_index = os.path.join(app.static_folder, '..', 'dist', 'index.html')
    if os.path.exists(vue_index):
        return app.send_static_file('../dist/index.html')
    # 否则使用传统模板（允许未登录用户访问）
    return render_template('index.html')

# 正版保障页面
@app.route('/feature/genuine')
def genuine_page():
    return render_template('feature_genuine.html')

# 低价转让页面
@app.route('/feature/low-price')
def low_price_page():
    return render_template('feature_low_price.html')

# 校园交易页面
@app.route('/feature/campus-trade')
def campus_trade_page():
    return render_template('feature_campus_trade.html')

# 9成新以上页面
@app.route('/feature/new-condition')
def new_condition_page():
    return render_template('feature_new_condition.html')

# 支持互换页面
@app.route('/feature/exchange')
def exchange_page():
    return render_template('feature_exchange.html')

@app.route('/admin')
def admin_page():
    # 检查用户是否已登录且是管理员
    if 'user_id' in session and session.get('is_admin'):
        username = session.get('username', 'admin')
        return render_template('admin.html', username=username)
    elif 'user_id' in session:
        # 已登录但不是管理员，重定向到首页
        return redirect(url_for('index'))
    else:
        # 未登录，重定向到登录页
        return redirect(url_for('login_page'))

@app.route('/admin/analytics')
def admin_analytics_page():
    if 'user_id' not in session:
        return redirect(url_for('login_page'))
    if not session.get('is_admin'):
        return redirect(url_for('index'))
    
    username = session.get('username', 'admin')
    books = [book.to_dict() for book in Book.query.all()]
    users = [user.to_dict() for user in User.query.all()]
    orders = [order.to_dict() for order in Order.query.all()]
    
    def safe_float(value):
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0
    
    category_counts = Counter(book.get('category', '其他') or '其他' for book in books)
    order_status_counts = Counter(order.get('status', 'pending') or 'pending' for order in orders)
    price_values = [safe_float(book.get('price', 0)) for book in books]
    
    recent_books = sorted(
        books,
        key=lambda b: b.get('created_at', ''),
        reverse=True
    )[:5]
    recent_books = [
        {
            'title': book.get('title', ''),
            'category': book.get('category', '其他'),
            'price': safe_float(book.get('price', 0)),
            'status': book.get('status', 'available'),
            'created_at': book.get('created_at', '')
        }
        for book in recent_books
    ]
    
    recent_orders = sorted(
        orders,
        key=lambda o: o.get('created_at', ''),
        reverse=True
    )[:5]
    recent_orders = [
        {
            'book_title': order.get('book_title', ''),
            'price': safe_float(order.get('price', 0)),
            'status': order.get('status', 'pending'),
            'created_at': order.get('created_at', '')
        }
        for order in recent_orders
    ]
    
    total_users = len(users)
    admin_users = sum(1 for user in users if user.get('is_admin'))
    student_users = total_users - admin_users
    
    analytics_data = {
        'summary': {
            'total_books': len(books),
            'total_users': total_users,
            'monthly_sales': get_monthly_sales_value(orders),
            'pending_reviews': get_pending_reviews_value(orders),
            'avg_price': round(sum(price_values) / len(price_values), 2) if price_values else 0
        },
        'books': {
            'by_category': dict(category_counts),
            'avg_price': round(sum(price_values) / len(price_values), 2) if price_values else 0,
            'recent': recent_books
        },
        'orders': {
            'total': len(orders),
            'status_breakdown': dict(order_status_counts),
            'recent': recent_orders
        },
        'users': {
            'admins': admin_users,
            'students': max(student_users, 0),
            'total': total_users
        }
    }
    
    return render_template('admin_analytics.html', analytics_data=analytics_data, username=username)

@app.route('/admin/settings')
def admin_settings_page():
    if 'user_id' not in session:
        return redirect(url_for('login_page'))
    if not session.get('is_admin'):
        return redirect(url_for('index'))
    
    # 读取系统设置
    settings = Setting.get_all_as_dict()
    if not settings:
        # 默认设置
        settings = {
            'systemName': '校园书递',
            'pageSize': 10,
            'cacheDays': 7,
            'enableRegister': True,
            'maintenanceMode': False,
            'sessionTimeout': 30,
            'requireStrongPassword': True,
            'enableEmailNotification': True,
            'enableSystemMessage': True
        }
    
    username = session.get('username', 'admin')
    return render_template('admin_settings.html', settings=settings, username=username)

@app.route('/admin/userManagement')
def admin_user_management_page():
    if 'user_id' not in session:
        return redirect(url_for('login_page'))
    if not session.get('is_admin'):
        return redirect(url_for('index'))
    
    username = session.get('username', 'admin')
    return render_template('userManagement.html', username=username)

@app.route('/admin/bookManagement')
def admin_book_management_page():
    if 'user_id' not in session:
        return redirect(url_for('login_page'))
    if not session.get('is_admin'):
        return redirect(url_for('index'))
    
    username = session.get('username', 'admin')
    return render_template('bookManagement.html', username=username)

# 书籍数量详情页面
@app.route('/admin/books')
def admin_books_page():
    if 'user_id' not in session:
        return redirect(url_for('login_page'))
    if not session.get('is_admin'):
        return redirect(url_for('index'))
    
    username = session.get('username', 'admin')
    return render_template('admin_books.html', username=username)

# 注册用户详情页面
@app.route('/admin/users')
def admin_users_list_page():
    if 'user_id' not in session:
        return redirect(url_for('login_page'))
    if not session.get('is_admin'):
        return redirect(url_for('index'))
    
    username = session.get('username', 'admin')
    return render_template('admin_users_list.html', username=username)

# 本月销量详情页面
@app.route('/admin/sales')
def admin_sales_page():
    if 'user_id' not in session:
        return redirect(url_for('login_page'))
    if not session.get('is_admin'):
        return redirect(url_for('index'))
    
    username = session.get('username', 'admin')
    return render_template('admin_sales.html', username=username)

# 待处理任务详情页面
@app.route('/admin/pending')
def admin_pending_page():
    if 'user_id' not in session:
        return redirect(url_for('login_page'))
    if not session.get('is_admin'):
        return redirect(url_for('index'))
    
    username = session.get('username', 'admin')
    return render_template('admin_pending.html', username=username)

# 健康检查接口
@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'ok', 'message': 'Service is running'})

# 系统信息接口
@app.route('/api/system/info', methods=['GET'])
def system_info():
    return jsonify({
        'name': '校园图书配送系统',
        'version': '1.0.0',
        'description': '为校园用户提供图书配送服务的系统'
    })

# 用户相关API
# 发送验证码接口
@app.route('/api/send_code', methods=['POST'])
def send_code():
    data = request.json
    phone = data.get('phone', '').strip()
    
    # 验证手机号格式
    if not phone or not re.match(r'^1[3-9]\d{9}$', phone):
        return jsonify({'success': False, 'message': '请输入有效的手机号码'}), 400
    
    # 测试验证码：666666（用于开发测试）
    # 实际项目中应该发送真实短信验证码
    test_code = '666666'
    
    # 将验证码存储到session中（实际项目中应该使用Redis等缓存）
    if 'verification_codes' not in session:
        session['verification_codes'] = {}
    session['verification_codes'][phone] = {
        'code': test_code,
        'expire_time': time.time() + 300  # 5分钟过期
    }
    session.modified = True
    
    return jsonify({
        'success': True, 
        'message': f'验证码已发送（测试验证码：{test_code}）',
        'code': test_code  # 仅用于测试，生产环境应移除
    })

# 注册接口
@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    
    # 检查必填字段
    if not data.get('username') or not data.get('password') or not data.get('phone'):
        return jsonify({'status': 'error', 'message': '请填写完整信息'}), 400
    
    # 验证验证码
    verify_code = data.get('verifyCode', '').strip()
    phone = data.get('phone', '').strip()
    
    # 检查验证码
    if not verify_code:
        return jsonify({'status': 'error', 'message': '请输入验证码'}), 400
    
    # 验证码验证逻辑
    verification_codes = session.get('verification_codes', {})
    phone_code_info = verification_codes.get(phone)
    
    # 测试验证码：666666 始终有效
    if verify_code != '666666':
        if not phone_code_info:
            return jsonify({'status': 'error', 'message': '请先获取验证码'}), 400
        
        if time.time() > phone_code_info['expire_time']:
            return jsonify({'status': 'error', 'message': '验证码已过期，请重新获取'}), 400
        
        if phone_code_info['code'] != verify_code:
            return jsonify({'status': 'error', 'message': '验证码错误'}), 400
    
    # 检查用户名是否已存在
    existing_user = User.query.filter_by(username=data['username']).first()
    if existing_user:
        return jsonify({'status': 'error', 'message': '用户名已存在'}), 400
    
    # 检查手机号是否已注册
    existing_phone = User.query.filter_by(phone=phone).first()
    if existing_phone:
        return jsonify({'status': 'error', 'message': '该手机号已被注册'}), 400
    
    # 创建新用户
    new_user = User(
        id=generate_id(),
        username=data['username'],
        password=hash_password(data['password']),
        email=data.get('email', ''),
        phone=phone,
        created_at=time.strftime('%Y-%m-%d %H:%M:%S'),
        is_admin=False
    )
    
    db.session.add(new_user)
    db.session.commit()
    
    # 同步数据到database文件夹
    sync_users_to_json()
    
    # 清除已使用的验证码
    if phone in verification_codes:
        del verification_codes[phone]
        session['verification_codes'] = verification_codes
        session.modified = True
    
    return jsonify({'status': 'success', 'message': '注册成功', 'user_id': new_user.id})

# 登录接口
@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    
    # 获取请求中的角色参数（如果有）
    requested_role = data.get('role', 'student')
    
    # 清理密码，去除可能的前后引号和特殊字符
    raw_password = data.get('password', '')
    cleaned_password = raw_password.strip()
    if (cleaned_password.startswith('\'') and cleaned_password.endswith('\'')) or \
       (cleaned_password.startswith('"') and cleaned_password.endswith('"')):
        cleaned_password = cleaned_password[1:-1].strip()
    
    # 查找用户
    user = User.query.filter_by(username=data['username']).first()
    if not user:
        return jsonify({'status': 'error', 'message': '用户名或密码错误'}), 401
    
    # 验证密码
    hashed_password = hash_password(cleaned_password)
    if hashed_password != user.password:
        return jsonify({'status': 'error', 'message': '用户名或密码错误'}), 401
    
    # 验证角色匹配
    is_admin_user = user.is_admin
    if requested_role == 'admin' and not is_admin_user:
        return jsonify({'status': 'error', 'message': '用户名或密码错误'}), 401
    if requested_role == 'student' and is_admin_user:
        return jsonify({'status': 'error', 'message': '用户名或密码错误'}), 401
    
    # 登录成功
    session['user_id'] = user.id
    session['username'] = user.username
    session['is_admin'] = is_admin_user
    return jsonify({
        'status': 'success', 
        'message': '登录成功',
        'user': {
            'id': user.id,
            'username': user.username,
            'is_admin': is_admin_user
        }
    })

# 登出接口
@app.route('/login')
def login_page():
    # 检查URL参数中是否有role=admin，如果有则允许管理员登录（即使已登录）
    role = request.args.get('role')
    # 如果已登录且不是管理员登录请求，重定向到首页
    if 'user_id' in session and role != 'admin':
        return redirect(url_for('index'))
    return render_template('login.html')

@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'status': 'success', 'message': '登出成功'})

# 获取当前用户信息
@app.route('/api/user/info', methods=['GET'])
def get_user_info():
    if not is_logged_in():
        return jsonify({'status': 'error', 'message': '请先登录'}), 401
    
    user = User.query.filter_by(id=str(session['user_id'])).first()
    if not user:
        return jsonify({'status': 'error', 'message': '用户不存在'}), 404
    
    return jsonify({
        'status': 'success',
        'user': user.to_dict()
    })

# 更新用户信息
@app.route('/api/user/info', methods=['PUT'])
def update_user_info():
    if not is_logged_in():
        return jsonify({'status': 'error', 'message': '请先登录'}), 401
    
    data = request.json
    user = User.query.filter_by(id=str(session['user_id'])).first()
    if not user:
        return jsonify({'status': 'error', 'message': '用户不存在'}), 404
    
    # 检查用户名是否已被其他用户使用
    new_username = data.get('username', '').strip()
    if new_username and new_username != user.username:
        existing = User.query.filter_by(username=new_username).first()
        if existing:
            return jsonify({'status': 'error', 'message': '用户名已被使用'}), 400
    
    # 更新允许修改的字段
    if 'username' in data:
        user.username = data['username'].strip()
    if 'school' in data:
        user.school = data.get('school', '').strip()
    if 'introduction' in data:
        user.introduction = data.get('introduction', '').strip()
    if 'avatar' in data:
        user.avatar = data.get('avatar', '').strip()
    
    user.updated_at = time.strftime('%Y-%m-%d %H:%M:%S')
    db.session.commit()
    
    # 同步用户数据到 JSON 文件
    sync_users_to_json()
    
    # 更新session中的用户名
    if 'username' in data:
        session['username'] = data['username'].strip()
    
    return jsonify({
        'status': 'success',
        'message': '信息更新成功',
        'user': user.to_dict()
    })

# 修改密码
@app.route('/api/user/password', methods=['PUT'])
def change_password():
    if not is_logged_in():
        return jsonify({'status': 'error', 'message': '请先登录'}), 401
    
    data = request.json
    old_password = data.get('oldPassword', '').strip()
    new_password = data.get('newPassword', '').strip()
    confirm_password = data.get('confirmPassword', '').strip()
    
    # 验证输入
    if not old_password or not new_password or not confirm_password:
        return jsonify({'status': 'error', 'message': '请填写所有密码字段'}), 400
    
    if new_password != confirm_password:
        return jsonify({'status': 'error', 'message': '两次输入的新密码不一致'}), 400
    
    if len(new_password) < 6:
        return jsonify({'status': 'error', 'message': '密码长度不能少于6位'}), 400
    
    user = User.query.filter_by(id=str(session['user_id'])).first()
    if not user:
        return jsonify({'status': 'error', 'message': '用户不存在'}), 404
    
    # 验证当前密码
    hashed_old_password = hash_password(old_password)
    if user.password != hashed_old_password:
        return jsonify({'status': 'error', 'message': '当前密码不正确'}), 400
    
    # 更新密码
    user.password = hash_password(new_password)
    user.updated_at = time.strftime('%Y-%m-%d %H:%M:%S')
    db.session.commit()
    
    return jsonify({'status': 'success', 'message': '密码修改成功'})

# 书籍相关API
# 获取书籍列表
@app.route('/api/books', methods=['GET'])
def get_books():
    # 获取查询参数
    page = int(request.args.get('page', 1))
    page_size = int(request.args.get('page_size', 1000))
    category = request.args.get('category')
    search = request.args.get('search', '').strip().lower()
    include_sold = request.args.get('include_sold', 'false').lower() == 'true'
    
    # 构建查询
    query = Book.query
    
    # 默认只显示在售的书籍
    if not include_sold and not session.get('is_admin'):
        query = query.filter_by(status='available')
    
    # 分类筛选
    if category and category != 'all':
        query = query.filter_by(category=category)
    
    # 搜索筛选
    if search:
        search_filter = db.or_(
            Book.title.contains(search),
            Book.author.contains(search),
            Book.owner_name.contains(search),
            Book.seller.contains(search)
        )
        query = query.filter(search_filter)
    
    # 获取所有结果用于价格筛选和总数
    all_books = [book.to_dict() for book in query.all()]
    
    # 按创建时间降序排序（新发布的书籍显示在最前面）
    def get_sort_time(book):
        """获取书籍的排序时间，优先使用created_at，其次createTime，最后publish_date"""
        time_str = book.get('created_at') or book.get('createTime') or book.get('publish_date') or ''
        if not time_str:
            return '1970-01-01 00:00:00'  # 如果没有时间，排到最后
        # 如果时间格式不完整，尝试补充
        if len(time_str) == 10:  # 只有日期，没有时间
            time_str += ' 00:00:00'
        return time_str
    
    all_books.sort(key=get_sort_time, reverse=True)  # reverse=True表示降序，最新的在前
    
    # 价格范围筛选
    price_range = request.args.get('priceRange')
    if price_range and price_range != 'all':
        filtered_books = []
        for book in all_books:
            price = float(book.get('price', 0))
            if price_range == '0-50' and 0 <= price <= 50:
                filtered_books.append(book)
            elif price_range == '50-100' and 50 < price <= 100:
                filtered_books.append(book)
            elif price_range == '100+' and price > 100:
                filtered_books.append(book)
        all_books = filtered_books
    
    # 分页
    start = (page - 1) * page_size
    end = start + page_size
    paginated_books = all_books[start:end]
    
    return jsonify({
        'status': 'success',
        'books': paginated_books,
        'total': len(all_books),
        'page': page,
        'page_size': page_size
    })

# 获取书籍详情
@app.route('/api/books/<book_id>', methods=['GET'])
def get_book_detail(book_id):
    try:
        book = Book.query.filter_by(id=str(book_id)).first()
        if not book:
            return jsonify({'status': 'error', 'message': '书籍不存在'}), 404
        return jsonify({'status': 'success', 'book': book.to_dict()})
    except Exception as e:
        print(f'获取书籍详情错误: {e}')
        return jsonify({'status': 'error', 'message': f'服务器错误: {str(e)}'}), 500

# 添加新书籍
@app.route('/api/books', methods=['POST'])
def add_book():
    if not is_logged_in():
        return jsonify({'status': 'error', 'message': '请先登录'}), 401
    
    data = request.json
    
    # 验证必填字段
    if not data.get('title') or not data.get('title').strip():
        return jsonify({'status': 'error', 'message': '书籍标题不能为空'}), 400
    
    if not data.get('category'):
        return jsonify({'status': 'error', 'message': '请选择书籍分类'}), 400
    
    if not data.get('price') or float(data.get('price', 0)) <= 0:
        return jsonify({'status': 'error', 'message': '价格必须大于0'}), 400
    
    if not data.get('desc') or not data.get('desc').strip():
        return jsonify({'status': 'error', 'message': '请填写书籍描述'}), 400
    
    if not data.get('contact') or not data.get('contact').strip():
        return jsonify({'status': 'error', 'message': '请填写联系方式'}), 400
    
    # 处理图片
    imgs = data.get('imgs', [])
    if not imgs or len(imgs) == 0:
        return jsonify({'status': 'error', 'message': '请至少上传一张图片'}), 400
    
    # 确保imgs是数组
    if isinstance(imgs, str):
        imgs = [imgs]
    
    # 获取用户信息
    user_id = str(session['user_id'])
    username = session.get('username', '')
    
    # 创建新书籍对象
    new_book = Book(
        id=generate_id(),
        title=data['title'].strip(),
        author=data.get('author', '').strip() or '未知作者',
        category=data.get('category', 'other'),
        price=float(data.get('price', 0)),
        desc=data.get('desc', '').strip(),
        description=data.get('desc', '').strip(),
        imgs=json.dumps(imgs, ensure_ascii=False),
        image=imgs[0] if imgs else '',
        cover_url=imgs[0] if imgs else '',
        contact=data.get('contact', '').strip(),
        stock=int(data.get('stock', 1)),
        status='available',
        owner_id=user_id,
        owner_name=username,
        seller=username,
        sellerId=user_id,
        createTime=time.strftime('%Y-%m-%d'),
        created_at=time.strftime('%Y-%m-%d %H:%M:%S'),
        publish_date=time.strftime('%Y-%m-%d')
    )
    
    db.session.add(new_book)
    db.session.commit()
    
    return jsonify({
        'status': 'success', 
        'message': '发布成功', 
        'book': new_book.to_dict(),
        'book_id': new_book.id
    })

# 更新书籍信息
@app.route('/api/books/<book_id>', methods=['PUT'])
def update_book(book_id):
    if not is_logged_in():
        return jsonify({'status': 'error', 'message': '请先登录'}), 401
    
    data = request.json
    book = Book.query.filter_by(id=str(book_id)).first()
    
    if not book:
        return jsonify({'status': 'error', 'message': '书籍不存在'}), 404
    
    # 检查权限：只有书籍所有者或管理员可以更新
    user_id = str(session['user_id'])
    owner_id = str(book.owner_id or book.sellerId or '')
    if owner_id != user_id and not session.get('is_admin'):
        return jsonify({'status': 'error', 'message': '无权限修改'}), 403
    
    # 验证必填字段
    if 'title' in data and (not data['title'] or not data['title'].strip()):
        return jsonify({'status': 'error', 'message': '书籍标题不能为空'}), 400
    
    if 'price' in data and (not data['price'] or float(data.get('price', 0)) <= 0):
        return jsonify({'status': 'error', 'message': '价格必须大于0'}), 400
    
    # 更新字段
    if 'title' in data:
        book.title = data['title'].strip()
    if 'author' in data:
        book.author = data.get('author', '').strip() or '未知作者'
    if 'category' in data:
        book.category = data['category']
    if 'price' in data:
        book.price = float(data['price'])
    if 'desc' in data:
        book.desc = data['desc'].strip()
        book.description = data['desc'].strip()
    if 'description' in data:
        book.description = data['description'].strip()
        book.desc = data['description'].strip()
    if 'contact' in data:
        book.contact = data['contact'].strip()
    if 'imgs' in data:
        imgs = data['imgs']
        if isinstance(imgs, str):
            imgs = [imgs]
        book.imgs = json.dumps(imgs, ensure_ascii=False)
        if imgs and len(imgs) > 0:
            book.image = imgs[0]
            book.cover_url = imgs[0]
    if 'stock' in data:
        book.stock = int(data.get('stock', 1))
    if 'status' in data:
        book.status = data['status']
    
    book.updated_at = time.strftime('%Y-%m-%d %H:%M:%S')
    db.session.commit()
    
    return jsonify({'status': 'success', 'message': '更新成功', 'book': book.to_dict()})

# 删除书籍
@app.route('/api/books/<book_id>', methods=['DELETE'])
def delete_book(book_id):
    if not is_logged_in():
        return jsonify({'status': 'error', 'message': '请先登录'}), 401
    
    book = Book.query.filter_by(id=str(book_id)).first()
    if not book:
        return jsonify({'status': 'error', 'message': '书籍不存在'}), 404
    
    # 检查权限：只有书籍所有者或管理员可以删除
    if str(book.owner_id) != str(session['user_id']) and not session.get('is_admin'):
        return jsonify({'status': 'error', 'message': '无权限删除'}), 403
    
    # 检查书籍是否已售出
    if book.status == 'sold':
        return jsonify({'status': 'error', 'message': '已售出的书籍不能删除'}), 400
    
    # 同时删除相关收藏
    Collection.query.filter_by(book_id=str(book_id)).delete()
    
    # 删除书籍
    db.session.delete(book)
    db.session.commit()
    
    return jsonify({'status': 'success', 'message': '删除成功'})

# 订单相关API
# 创建订单
@app.route('/api/orders', methods=['POST'])
def create_order():
    if not is_logged_in():
        return jsonify({'status': 'error', 'message': '请先登录'}), 401
    
    data = request.json
    book = Book.query.filter_by(id=str(data.get('book_id', ''))).first()
    
    if not book:
        return jsonify({'status': 'error', 'message': '书籍不存在'}), 404
    
    if book.status != 'available':
        return jsonify({'status': 'error', 'message': '书籍已售出'}), 400
    
    owner_id = str(book.owner_id or book.sellerId or '')
    if owner_id == str(session['user_id']):
        return jsonify({'status': 'error', 'message': '不能购买自己的书籍'}), 400
    
    # 创建订单
    new_order = Order(
        id=generate_id(),
        book_id=str(book.id),
        book_title=book.title,
        buyer_id=str(session['user_id']),
        buyer_name=session.get('username', ''),
        seller_id=owner_id,
        seller_name=book.owner_name or book.seller or '',
        price=float(book.price),
        status='pending',
        created_at=time.strftime('%Y-%m-%d %H:%M:%S')
    )
    
    db.session.add(new_order)
    
    # 更新书籍状态
    book.status = 'sold'
    db.session.commit()
    
    return jsonify({'status': 'success', 'message': '订单创建成功', 'order': new_order.to_dict()})

# 获取订单列表
@app.route('/api/orders', methods=['GET'])
def get_orders():
    if not is_logged_in():
        return jsonify({'status': 'error', 'message': '请先登录'}), 401
    
    user_id = str(session['user_id'])
    
    # 如果是管理员，返回所有订单
    if session.get('is_admin'):
        orders = [order.to_dict() for order in Order.query.all()]
    else:
        # 否则只返回用户作为买家或卖家的订单
        orders = [order.to_dict() for order in Order.query.filter(
            db.or_(Order.buyer_id == user_id, Order.seller_id == user_id)
        ).all()]
    
    return jsonify({'status': 'success', 'orders': orders})

# 获取单个订单详情
@app.route('/api/orders/<order_id>', methods=['GET'])
def get_order_detail(order_id):
    if not is_logged_in():
        return jsonify({'status': 'error', 'message': '请先登录'}), 401
    
    order = Order.query.filter_by(id=str(order_id)).first()
    
    if not order:
        return jsonify({'status': 'error', 'message': '订单不存在'}), 404
    
    user_id = str(session['user_id'])
    order_buyer_id = str(order.buyer_id or '')
    order_seller_id = str(order.seller_id or '')
    
    # 检查权限：只有订单的买卖双方或管理员可以查看
    if not session.get('is_admin') and user_id != order_buyer_id and user_id != order_seller_id:
        return jsonify({'status': 'error', 'message': '无权查看此订单'}), 403
    
    return jsonify({'status': 'success', 'order': order.to_dict()})

# 更新订单状态
@app.route('/api/orders/<order_id>/status', methods=['PUT'])
def update_order_status(order_id):
    if not is_logged_in():
        return jsonify({'status': 'error', 'message': '请先登录'}), 401
    
    order = Order.query.filter_by(id=str(order_id)).first()
    
    if not order:
        return jsonify({'status': 'error', 'message': '订单不存在'}), 404
    
    user_id = str(session['user_id'])
    order_buyer_id = str(order.buyer_id or '')
    order_seller_id = str(order.seller_id or '')
    
    # 检查权限
    if not session.get('is_admin') and user_id != order_buyer_id and user_id != order_seller_id:
        return jsonify({'status': 'error', 'message': '无权操作此订单'}), 403
    
    data = request.json
    new_status = data.get('status')
    
    # 验证状态转换
    current_status = order.status or 'pending'
    valid_transitions = {
        'pending': ['shipped', 'cancelled'],
        'shipped': ['completed'],
        'completed': [],
        'cancelled': []
    }
    
    if new_status not in valid_transitions.get(current_status, []):
        return jsonify({'status': 'error', 'message': '无效的状态转换'}), 400
    
    # 检查操作权限
    if new_status == 'shipped' and user_id != order_seller_id:
        return jsonify({'status': 'error', 'message': '只有卖家可以标记已发货'}), 403
    
    if new_status == 'completed' and user_id != order_buyer_id:
        return jsonify({'status': 'error', 'message': '只有买家可以确认收货'}), 403
    
    # 更新状态
    order.status = new_status
    db.session.commit()
    
    return jsonify({'status': 'success', 'message': '订单状态更新成功', 'order': order.to_dict()})

# 收藏相关API
# 检查收藏状态
@app.route('/api/collections/check/<book_id>', methods=['GET'])
def check_collection(book_id):
    if not is_logged_in():
        return jsonify({'status': 'error', 'message': '请先登录'}), 401
    
    user_id = str(session['user_id'])
    collection = Collection.query.filter_by(
        book_id=str(book_id),
        user_id=user_id
    ).first()
    
    return jsonify({
        'status': 'success',
        'is_collected': collection is not None
    })

# 收藏/取消收藏
@app.route('/api/collections/<book_id>', methods=['POST'])
def toggle_collection(book_id):
    if not is_logged_in():
        return jsonify({'status': 'error', 'message': '请先登录'}), 401
    
    user_id = str(session['user_id'])
    book_id_str = str(book_id)
    
    # 检查是否已收藏
    collection = Collection.query.filter_by(
        book_id=book_id_str,
        user_id=user_id
    ).first()
    
    if collection:
        # 取消收藏
        db.session.delete(collection)
        db.session.commit()
        return jsonify({'status': 'success', 'message': '取消收藏成功', 'is_collected': False})
    
    # 添加收藏
    new_collection = Collection(
        id=generate_id(),
        book_id=book_id_str,
        user_id=user_id,
        username=session.get('username', ''),
        created_at=time.strftime('%Y-%m-%d %H:%M:%S')
    )
    
    db.session.add(new_collection)
    db.session.commit()
    
    return jsonify({'status': 'success', 'message': '收藏成功', 'is_collected': True})

# 获取用户收藏列表
@app.route('/api/collections', methods=['GET'])
def get_collections():
    if not is_logged_in():
        return jsonify({'status': 'error', 'message': '请先登录'}), 401
    
    user_id = str(session['user_id'])
    user_collections = Collection.query.filter_by(user_id=user_id).all()
    
    # 获取收藏的书籍详情
    collected_books = []
    for collection in user_collections:
        book = Book.query.filter_by(id=str(collection.book_id)).first()
        if book:
            collected_books.append(book.to_dict())
    
    return jsonify({'status': 'success', 'collections': collected_books, 'books': collected_books})

# 评论相关API
# 获取书籍评论列表
@app.route('/api/comments/<book_id>', methods=['GET'])
def get_comments(book_id):
    try:
        comments_file = os.path.join(DB_DIR, 'comments.json')
        if not os.path.exists(comments_file):
            return jsonify({'status': 'success', 'comments': []})
        
        with open(comments_file, 'r', encoding='utf-8') as f:
            all_comments = json.load(f)
        
        # 筛选出该书籍的评论，按时间倒序排列
        book_comments = [
            comment for comment in all_comments 
            if str(comment.get('book_id')) == str(book_id)
        ]
        book_comments.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        
        return jsonify({'status': 'success', 'comments': book_comments})
    except Exception as e:
        print(f'获取评论列表错误: {e}')
        return jsonify({'status': 'error', 'message': f'服务器错误: {str(e)}'}), 500

# 添加评论
@app.route('/api/comments', methods=['POST'])
def add_comment():
    if not is_logged_in():
        return jsonify({'status': 'error', 'message': '请先登录'}), 401
    
    data = request.json
    book_id = str(data.get('book_id', ''))
    content = data.get('content', '').strip()
    
    # 验证必填字段
    if not book_id:
        return jsonify({'status': 'error', 'message': '书籍ID不能为空'}), 400
    
    if not content:
        return jsonify({'status': 'error', 'message': '评论内容不能为空'}), 400
    
    if len(content) > 1000:
        return jsonify({'status': 'error', 'message': '评论内容不能超过1000字'}), 400
    
    # 检查书籍是否存在
    book = Book.query.filter_by(id=book_id).first()
    if not book:
        return jsonify({'status': 'error', 'message': '书籍不存在'}), 404
    
    try:
        comments_file = os.path.join(DB_DIR, 'comments.json')
        
        # 确保目录存在
        os.makedirs(DB_DIR, exist_ok=True)
        
        # 读取现有评论
        if os.path.exists(comments_file):
            with open(comments_file, 'r', encoding='utf-8') as f:
                all_comments = json.load(f)
        else:
            all_comments = []
        
        # 创建新评论
        user_id = str(session['user_id'])
        username = session.get('username', '匿名用户')
        
        new_comment = {
            'id': generate_id(),
            'book_id': book_id,
            'book_title': book.title,
            'user_id': user_id,
            'username': username,
            'content': content,
            'created_at': time.strftime('%Y-%m-%d %H:%M:%S'),
            'likes': 0,
            'is_deleted': False
        }
        
        all_comments.append(new_comment)
        
        # 保存到文件
        with open(comments_file, 'w', encoding='utf-8') as f:
            json.dump(all_comments, f, ensure_ascii=False, indent=2)
        
        return jsonify({
            'status': 'success', 
            'message': '评论发表成功',
            'comment': new_comment
        })
    except Exception as e:
        print(f'添加评论错误: {e}')
        return jsonify({'status': 'error', 'message': f'服务器错误: {str(e)}'}), 500

# 删除评论
@app.route('/api/comments/<comment_id>', methods=['DELETE'])
def delete_comment(comment_id):
    if not is_logged_in():
        return jsonify({'status': 'error', 'message': '请先登录'}), 401
    
    try:
        comments_file = os.path.join(DB_DIR, 'comments.json')
        if not os.path.exists(comments_file):
            return jsonify({'status': 'error', 'message': '评论不存在'}), 404
        
        with open(comments_file, 'r', encoding='utf-8') as f:
            all_comments = json.load(f)
        
        # 查找评论
        comment = next((c for c in all_comments if str(c.get('id')) == str(comment_id)), None)
        if not comment:
            return jsonify({'status': 'error', 'message': '评论不存在'}), 404
        
        user_id = str(session['user_id'])
        is_admin = session.get('is_admin', False)
        
        # 检查权限：只能删除自己的评论或管理员可以删除任何评论
        if str(comment.get('user_id')) != user_id and not is_admin:
            return jsonify({'status': 'error', 'message': '无权限删除此评论'}), 403
        
        # 删除评论（软删除，标记为已删除）
        comment['is_deleted'] = True
        
        # 保存到文件
        with open(comments_file, 'w', encoding='utf-8') as f:
            json.dump(all_comments, f, ensure_ascii=False, indent=2)
        
        return jsonify({'status': 'success', 'message': '评论删除成功'})
    except Exception as e:
        print(f'删除评论错误: {e}')
        return jsonify({'status': 'error', 'message': f'服务器错误: {str(e)}'}), 500

# 评价相关API
# 提交评价
@app.route('/api/reviews', methods=['POST'])
def submit_review():
    if not is_logged_in():
        return jsonify({'status': 'error', 'message': '请先登录'}), 401
    
    try:
        data = request.json
        order_id = str(data.get('order_id', ''))
        reviewed_user_id = str(data.get('reviewed_user_id', ''))
        reviewer_role = data.get('reviewer_role', '')  # 'buyer' or 'seller'
        service_rating = int(data.get('service_rating', 0))
        condition_rating = int(data.get('condition_rating', 0))
        efficiency_rating = int(data.get('efficiency_rating', 0))
        review_content = data.get('review_content', '').strip()
        
        # 验证评分范围
        if not all(1 <= rating <= 5 for rating in [service_rating, condition_rating, efficiency_rating]):
            return jsonify({'status': 'error', 'message': '评分必须在1-5之间'}), 400
        
        # 验证订单是否存在且已完成
        order = Order.query.filter_by(id=order_id).first()
        if not order:
            return jsonify({'status': 'error', 'message': '订单不存在'}), 404
        
        if order.status != 'completed':
            return jsonify({'status': 'error', 'message': '只有已完成的订单才能评价'}), 400
        
        # 验证评价者身份
        user_id = str(session['user_id'])
        order_buyer_id = str(order.buyer_id or '')
        order_seller_id = str(order.seller_id or '')
        
        if reviewer_role == 'buyer' and user_id != order_buyer_id:
            return jsonify({'status': 'error', 'message': '只有买家可以评价卖家'}), 403
        
        if reviewer_role == 'seller' and user_id != order_seller_id:
            return jsonify({'status': 'error', 'message': '只有卖家可以评价买家'}), 403
        
        # 检查是否已评价
        reviews_file = os.path.join(DB_DIR, 'reviews.json')
        reviews = []
        if os.path.exists(reviews_file):
            with open(reviews_file, 'r', encoding='utf-8') as f:
                reviews = json.load(f)
        
        # 检查是否已经评价过
        existing_review = next((
            r for r in reviews 
            if str(r.get('order_id')) == order_id and str(r.get('reviewer_id')) == user_id
        ), None)
        
        if existing_review:
            return jsonify({'status': 'error', 'message': '您已经评价过此订单'}), 400
        
        # 创建评价
        review = {
            'id': generate_id(),
            'order_id': order_id,
            'book_id': str(order.book_id),
            'reviewer_id': user_id,
            'reviewer_name': session.get('username', ''),
            'reviewer_role': reviewer_role,
            'reviewed_user_id': reviewed_user_id,
            'service_rating': service_rating,
            'condition_rating': condition_rating,
            'efficiency_rating': efficiency_rating,
            'review_content': review_content,
            'created_at': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        reviews.append(review)
        
        # 保存到文件
        os.makedirs(DB_DIR, exist_ok=True)
        with open(reviews_file, 'w', encoding='utf-8') as f:
            json.dump(reviews, f, ensure_ascii=False, indent=2)
        
        return jsonify({'status': 'success', 'message': '评价提交成功', 'review': review})
    except Exception as e:
        print(f'提交评价错误: {e}')
        return jsonify({'status': 'error', 'message': f'服务器错误: {str(e)}'}), 500

# 获取订单的评价
@app.route('/api/reviews/order/<order_id>', methods=['GET'])
def get_order_reviews(order_id):
    if not is_logged_in():
        return jsonify({'status': 'error', 'message': '请先登录'}), 401
    
    try:
        # 验证订单权限
        order = Order.query.filter_by(id=str(order_id)).first()
        if not order:
            return jsonify({'status': 'error', 'message': '订单不存在'}), 404
        
        user_id = str(session['user_id'])
        order_buyer_id = str(order.buyer_id or '')
        order_seller_id = str(order.seller_id or '')
        
        # 检查权限：只有订单的买卖双方或管理员可以查看
        if not session.get('is_admin') and user_id != order_buyer_id and user_id != order_seller_id:
            return jsonify({'status': 'error', 'message': '无权查看此订单的评价'}), 403
        
        # 读取评价数据
        reviews_file = os.path.join(DB_DIR, 'reviews.json')
        if not os.path.exists(reviews_file):
            return jsonify({'status': 'success', 'reviews': []})
        
        with open(reviews_file, 'r', encoding='utf-8') as f:
            all_reviews = json.load(f)
        
        # 筛选该订单的评价
        order_reviews = [
            r for r in all_reviews 
            if str(r.get('order_id')) == str(order_id)
        ]
        
        return jsonify({'status': 'success', 'reviews': order_reviews})
    except Exception as e:
        print(f'获取评价错误: {e}')
        return jsonify({'status': 'error', 'message': f'服务器错误: {str(e)}'}), 500

# 管理员功能
# 获取所有用户列表
@app.route('/api/admin/users', methods=['GET'])
def get_all_users():
    if not is_admin():
        return jsonify({'status': 'error', 'message': '无管理员权限'}), 403
    
    users = [user.to_dict() for user in User.query.all()]
    return jsonify({'status': 'success', 'users': users})

# 管理员创建用户
@app.route('/api/admin/users', methods=['POST'])
def admin_create_user():
    if not is_admin():
        return jsonify({'status': 'error', 'message': '无管理员权限'}), 403
    
    data = request.json
    
    # 验证必填字段
    if not data.get('username'):
        return jsonify({'status': 'error', 'message': '用户名不能为空'}), 400
    if not data.get('password'):
        return jsonify({'status': 'error', 'message': '密码不能为空'}), 400
    
    # 检查用户名是否已存在
    existing = User.query.filter_by(username=data['username']).first()
    if existing:
        return jsonify({'status': 'error', 'message': '用户名已存在'}), 400
    
    # 创建新用户
    new_user = User(
        id=generate_id(),
        username=data['username'],
        password=hash_password(data['password']),
        email=data.get('email', ''),
        phone=data.get('phone', ''),
        created_at=time.strftime('%Y-%m-%d %H:%M:%S'),
        is_admin=data.get('role') == 'admin' or data.get('is_admin', False)
    )
    
    db.session.add(new_user)
    db.session.commit()
    
    return jsonify({'status': 'success', 'message': '用户创建成功', 'user': new_user.to_dict()})

# 管理员更新用户
@app.route('/api/admin/users/<user_id>', methods=['PUT'])
def admin_update_user(user_id):
    if not is_admin():
        return jsonify({'status': 'error', 'message': '无管理员权限'}), 403
    
    data = request.json
    user = User.query.filter_by(id=str(user_id)).first()
    
    if not user:
        return jsonify({'status': 'error', 'message': '用户不存在'}), 404
    
    # 检查用户名是否已被其他用户使用
    new_username = data.get('username', '').strip()
    if new_username and new_username != user.username:
        existing = User.query.filter_by(username=new_username).first()
        if existing:
            return jsonify({'status': 'error', 'message': '用户名已被使用'}), 400
    
    # 更新允许修改的字段
    if 'username' in data:
        user.username = data['username'].strip()
    if 'email' in data:
        user.email = data.get('email', '').strip()
    if 'phone' in data:
        user.phone = data.get('phone', '').strip()
    if 'password' in data and data['password']:
        user.password = hash_password(data['password'])
    if 'role' in data:
        user.is_admin = data['role'] == 'admin'
    
    user.updated_at = time.strftime('%Y-%m-%d %H:%M:%S')
    db.session.commit()
    
    # 同步用户数据到 JSON 文件
    sync_users_to_json()
    
    return jsonify({
        'status': 'success',
        'message': '用户更新成功',
        'user': user.to_dict()
    })

# 管理员删除用户
@app.route('/api/admin/users/<user_id>', methods=['DELETE'])
def admin_delete_user(user_id):
    if not is_admin():
        return jsonify({'status': 'error', 'message': '无管理员权限'}), 403
    
    user = User.query.filter_by(id=str(user_id)).first()
    
    if not user:
        return jsonify({'status': 'error', 'message': '用户不存在'}), 404
    
    # 不能删除自己
    if str(user_id) == str(session.get('user_id')):
        return jsonify({'status': 'error', 'message': '不能删除自己的账户'}), 400
    
    db.session.delete(user)
    db.session.commit()
    
    # 同步用户数据到 JSON 文件
    sync_users_to_json()
    
    return jsonify({
        'status': 'success',
        'message': '用户删除成功'
    })

# 获取所有订单列表
@app.route('/api/admin/orders', methods=['GET'])
def get_all_orders():
    if not is_admin():
        return jsonify({'status': 'error', 'message': '无管理员权限'}), 403
    
    orders = [order.to_dict() for order in Order.query.all()]
    return jsonify({'status': 'success', 'orders': orders})

# 管理员仪表盘统计数据
@app.route('/api/admin/stats', methods=['GET'])
def get_admin_stats():
    if not is_admin():
        return jsonify({'status': 'error', 'message': '无管理员权限'}), 403
    
    books_count = Book.query.count()
    users_count = User.query.count()
    orders = [order.to_dict() for order in Order.query.all()]
    
    monthly_sales = get_monthly_sales_value(orders)
    pending_tasks = get_pending_reviews_value(orders)
    
    return jsonify({
        'status': 'success',
        'stats': {
            'totalBooks': books_count,
            'registeredUsers': users_count,
            'monthlySales': monthly_sales,
            'pendingTasks': pending_tasks
        }
    })

# 获取系统设置
@app.route('/api/admin/settings', methods=['GET'])
def get_admin_settings():
    if not is_admin():
        return jsonify({'status': 'error', 'message': '无管理员权限'}), 403
    
    settings = Setting.get_all_as_dict()
    if not settings:
        settings = {
            'systemName': '校园书递',
            'pageSize': 10,
            'cacheDays': 7,
            'enableRegister': True,
            'maintenanceMode': False,
            'sessionTimeout': 30,
            'requireStrongPassword': True,
            'enableEmailNotification': True,
            'enableSystemMessage': True
        }
    
    return jsonify({'status': 'success', 'settings': settings})

# 保存系统设置
@app.route('/api/admin/settings', methods=['POST'])
def save_admin_settings():
    if not is_admin():
        return jsonify({'status': 'error', 'message': '无管理员权限'}), 403
    
    data = request.json
    
    # 验证和清理数据
    settings_dict = {
        'systemName': data.get('systemName', '校园书递'),
        'pageSize': max(5, min(50, int(data.get('pageSize', 10)))),
        'cacheDays': max(1, min(30, int(data.get('cacheDays', 7)))),
        'enableRegister': bool(data.get('enableRegister', True)),
        'maintenanceMode': bool(data.get('maintenanceMode', False)),
        'sessionTimeout': max(5, min(1440, int(data.get('sessionTimeout', 30)))),
        'requireStrongPassword': bool(data.get('requireStrongPassword', True)),
        'enableEmailNotification': bool(data.get('enableEmailNotification', True)),
        'enableSystemMessage': bool(data.get('enableSystemMessage', True))
    }
    
    # 保存每个设置项
    for key, value in settings_dict.items():
        Setting.set_value(key, value)
    
    # 更新 updated_at
    Setting.set_value('updated_at', time.strftime('%Y-%m-%d %H:%M:%S'))
    
    return jsonify({'status': 'success', 'message': '设置保存成功', 'settings': settings_dict})

# 购物车相关API
# 获取购物车
@app.route('/api/cart', methods=['GET'])
def get_cart():
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': '请先登录'}), 401
    
    user_id = str(session['user_id'])
    user_cart = CartItem.query.filter_by(user_id=user_id).all()
    
    # 获取书籍详情
    cart_items = []
    for item in user_cart:
        item_dict = item.to_dict()
        book = Book.query.filter_by(id=str(item.book_id)).first()
        if book:
            book_dict = book.to_dict()
            item_dict['book'] = {
                'id': book_dict['id'],
                'title': book_dict.get('title', ''),
                'author': book_dict.get('author', ''),
                'price': book_dict.get('price', 0),
                'cover_url': book_dict.get('cover_url') or (book_dict.get('imgs', [])[0] if book_dict.get('imgs') else '') or book_dict.get('image', ''),
                'status': book_dict.get('status', 'available')
            }
        cart_items.append(item_dict)
    
    return jsonify({'status': 'success', 'cart': cart_items})

# 添加到购物车
@app.route('/api/cart', methods=['POST'])
def add_to_cart():
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': '请先登录'}), 401
    
    data = request.json
    book_id = data.get('book_id')
    quantity = int(data.get('quantity', 1))
    
    if not book_id:
        return jsonify({'status': 'error', 'message': '书籍ID不能为空'}), 400
    
    # 检查书籍是否存在
    book = Book.query.filter_by(id=str(book_id)).first()
    if not book:
        return jsonify({'status': 'error', 'message': '书籍不存在'}), 404
    
    if book.status != 'available':
        return jsonify({'status': 'error', 'message': '该书籍暂不可购买'}), 400
    
    # 检查是否添加自己的书
    owner_id = str(book.owner_id or book.sellerId or '')
    if owner_id == str(session['user_id']):
        return jsonify({'status': 'error', 'message': '不能添加自己发布的书籍到购物车'}), 400
    
    user_id = str(session['user_id'])
    book_id_str = str(book_id)
    
    # 检查是否已在购物车中
    existing_item = CartItem.query.filter_by(
        user_id=user_id,
        book_id=book_id_str
    ).first()
    
    if existing_item:
        existing_item.quantity = min(existing_item.quantity + quantity, 10)
        existing_item.updated_at = time.strftime('%Y-%m-%d %H:%M:%S')
    else:
        new_item = CartItem(
            id=generate_id(),
            user_id=user_id,
            book_id=book_id_str,
            quantity=quantity,
            created_at=time.strftime('%Y-%m-%d %H:%M:%S'),
            updated_at=time.strftime('%Y-%m-%d %H:%M:%S')
        )
        db.session.add(new_item)
    
    db.session.commit()
    return jsonify({'status': 'success', 'message': '已添加到购物车'})

# 更新购物车商品数量
@app.route('/api/cart/<item_id>', methods=['PUT'])
def update_cart_item(item_id):
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': '请先登录'}), 401
    
    data = request.json
    quantity = int(data.get('quantity', 1))
    
    if quantity < 1 or quantity > 10:
        return jsonify({'status': 'error', 'message': '数量必须在1-10之间'}), 400
    
    item = CartItem.query.filter_by(
        id=str(item_id),
        user_id=str(session['user_id'])
    ).first()
    
    if not item:
        return jsonify({'status': 'error', 'message': '购物车商品不存在'}), 404
    
    item.quantity = quantity
    item.updated_at = time.strftime('%Y-%m-%d %H:%M:%S')
    db.session.commit()
    
    return jsonify({'status': 'success', 'message': '更新成功'})

# 删除购物车商品
@app.route('/api/cart/<item_id>', methods=['DELETE'])
def delete_cart_item(item_id):
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': '请先登录'}), 401
    
    item = CartItem.query.filter_by(
        id=str(item_id),
        user_id=str(session['user_id'])
    ).first()
    
    if not item:
        return jsonify({'status': 'error', 'message': '购物车商品不存在'}), 404
    
    db.session.delete(item)
    db.session.commit()
    
    return jsonify({'status': 'success', 'message': '删除成功'})

# 清空购物车
@app.route('/api/cart', methods=['DELETE'])
def clear_cart():
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': '请先登录'}), 401
    
    CartItem.query.filter_by(user_id=str(session['user_id'])).delete()
    db.session.commit()
    
    return jsonify({'status': 'success', 'message': '购物车已清空'})

# 购物车页面
@app.route('/cart')
def cart_page():
    if 'user_id' not in session:
        return redirect(url_for('login_page'))
    return render_template('cart.html')

@app.route('/transactionHistory')
def transaction_history_page():
    if 'user_id' not in session:
        return redirect(url_for('login_page'))
    return render_template('transactionHistory.html')

@app.route('/orderDetails')
def order_details_page():
    if 'user_id' not in session:
        return redirect(url_for('login_page'))
    return render_template('orderDetails.html')

@app.route('/accountSettings')
def account_settings_page():
    if 'user_id' not in session:
        return redirect(url_for('login_page'))
    return render_template('accountSettings.html')

@app.route('/publishBook')
def publish_book_page():
    if 'user_id' not in session:
        return redirect(url_for('login_page'))
    return render_template('publishBook.html')

# 错误处理 - 支持Vue SPA路由
@app.errorhandler(404)
def page_not_found(e):
    # API路由直接返回404
    if request.path.startswith('/api/'):
        return jsonify({'status': 'error', 'message': 'API接口不存在'}), 404
    
    # 静态文件请求
    if request.path.startswith('/static/'):
        if request.path.endswith('.css'):
            if 'utils/variables.css' in request.path:
                return redirect(url_for('static', filename='css/variables.css'))
            elif 'utils/base.css' in request.path:
                return redirect(url_for('static', filename='css/base.css'))
            elif 'components/navbar.css' in request.path:
                return redirect(url_for('static', filename='css/navbar.css'))
        return jsonify({'status': 'error', 'message': '静态文件不存在'}), 404
    
    # Vue SPA路由 - 返回index.html让Vue Router处理
    vue_index = os.path.join(app.static_folder, '..', 'dist', 'index.html')
    if os.path.exists(vue_index):
        return app.send_static_file('../dist/index.html')
    
    # 传统模板路由
    path = request.path.strip('/')
    if path and os.path.exists(os.path.join(app.template_folder, f'{path}.html')):
        return render_template(f'{path}.html')
    
    return jsonify({'status': 'error', 'message': '页面不存在'}), 404

if __name__ == '__main__':
    # 初始化数据库
    with app.app_context():
        db.create_all()
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
    
    # 运行应用
    app.run(debug=True, host='0.0.0.0', port=5000)