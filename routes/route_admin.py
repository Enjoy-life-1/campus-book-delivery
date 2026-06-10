"""管理端核心 API"""
import time

from flask import jsonify, request, session

from models import db, User, Book, Order, Comment, Report, Setting
from security import hash_password


def register_admin_routes(app, helpers):
    """管理端：用户 CRUD、订单导出、仪表盘统计、系统设置"""
    generate_id = helpers['generate_id']
    is_logged_in = helpers['is_logged_in']
    is_admin = helpers['is_admin']
    is_full_admin = helpers['is_full_admin']
    get_monthly_sales_value = helpers['get_monthly_sales_value']
    get_pending_reviews_value = helpers['get_pending_reviews_value']
    orders_csv_response = helpers['orders_csv_response']
    app_ref = helpers.get('app') or app

    # 管理员功能
    # 获取所有用户列表
    @app.route('/api/admin/users', methods=['GET'])
    def get_all_users():
        """管理员用户列表"""
        if not is_admin():
            return jsonify({'status': 'error', 'message': '无管理员权限'}), 403
    
        users = [user.to_dict() for user in User.query.all()]
        return jsonify({'status': 'success', 'users': users})

    # 管理员创建用户
    @app.route('/api/admin/users', methods=['POST'])
    def admin_create_user():
        """超级管理员创建用户"""
        if not is_full_admin():
            return jsonify({'status': 'error', 'message': '需要超级管理员权限'}), 403
    
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
    
        role = (data.get('role') or 'student').strip()
        if role not in ('student', 'moderator', 'admin'):
            role = 'student'
        new_user = User(
            id=generate_id(),
            username=data['username'],
            password=hash_password(data['password']),
            email=data.get('email', ''),
            phone=data.get('phone', ''),
            created_at=time.strftime('%Y-%m-%d %H:%M:%S'),
            role=role,
            is_admin=(role == 'admin')
        )
    
        db.session.add(new_user)
        db.session.commit()
    
        return jsonify({'status': 'success', 'message': '用户创建成功', 'user': new_user.to_dict()})

    # 管理员更新用户
    @app.route('/api/admin/users/<user_id>', methods=['PUT'])
    def admin_update_user(user_id):
        """更新用户资料/角色/密码"""
        if not is_full_admin():
            return jsonify({'status': 'error', 'message': '需要超级管理员权限'}), 403
    
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
            role = (data.get('role') or 'student').strip()
            if role in ('student', 'moderator', 'admin'):
                user.role = role
                user.is_admin = (role == 'admin')

        user.updated_at = time.strftime('%Y-%m-%d %H:%M:%S')
        db.session.commit()

        return jsonify({
            'status': 'success',
            'message': '用户更新成功',
            'user': user.to_dict()
        })

    # 管理员删除用户
    @app.route('/api/admin/users/<user_id>', methods=['DELETE'])
    def admin_delete_user(user_id):
        """删除用户（不可删自己）"""
        if not is_full_admin():
            return jsonify({'status': 'error', 'message': '需要超级管理员权限'}), 403
    
        user = User.query.filter_by(id=str(user_id)).first()
    
        if not user:
            return jsonify({'status': 'error', 'message': '用户不存在'}), 404
    
        # 不能删除自己
        if str(user_id) == str(session.get('user_id')):
            return jsonify({'status': 'error', 'message': '不能删除自己的账户'}), 400
    
        db.session.delete(user)
        db.session.commit()

        return jsonify({
            'status': 'success',
            'message': '用户删除成功'
        })

    # 获取所有订单列表
    @app.route('/api/admin/orders', methods=['GET'])
    def get_all_orders():
        """全站订单"""
        if not is_admin():
            return jsonify({'status': 'error', 'message': '无管理员权限'}), 403
    
        orders = [order.to_dict() for order in Order.query.all()]
        return jsonify({'status': 'success', 'orders': orders})


    @app.route('/api/admin/export/orders', methods=['GET'])
    def admin_export_orders_csv():
        """导出订单 CSV"""
        if not is_admin():
            return jsonify({'status': 'error', 'message': '无管理员权限'}), 403
        orders = Order.query.order_by(Order.created_at.desc()).all()
        return orders_csv_response(orders, 'all_orders.csv')


    # 管理员仪表盘统计数据
    @app.route('/api/admin/stats', methods=['GET'])
    def get_admin_stats():
        """仪表盘：书籍/用户/月销/待审评论举报等"""
        if not is_admin():
            return jsonify({'status': 'error', 'message': '无管理员权限'}), 403
    
        books_count = Book.query.count()
        users_count = User.query.count()
        orders = [order.to_dict() for order in Order.query.all()]
    
        monthly_sales = get_monthly_sales_value(orders)
        pending_tasks = get_pending_reviews_value(orders)
        verified_users = User.query.filter_by(campus_verified=True).count()
        exchange_orders = Order.query.filter_by(order_type='exchange').count()
        pending_comments = Comment.query.filter_by(audit_status='pending', is_deleted=False).count()
        pending_reports = Report.query.filter_by(status='pending').count()

        return jsonify({
            'status': 'success',
            'stats': {
                'totalBooks': books_count,
                'registeredUsers': users_count,
                'monthlySales': monthly_sales,
                'pendingTasks': pending_tasks,
                'verifiedUsers': verified_users,
                'exchangeOrders': exchange_orders,
                'pendingComments': pending_comments,
                'pendingReports': pending_reports
            }
        })

    # 获取系统设置
    @app.route('/api/admin/settings', methods=['GET'])
    def get_admin_settings():
        """读取 Setting KV"""
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
        """持久化系统配置（含 ISBN/SMS/邮件 webhook 密钥）"""
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
            'enableSystemMessage': bool(data.get('enableSystemMessage', True)),
            'notify_email_enabled': bool(data.get('notify_email_enabled', data.get('enableEmailNotification', True))),
            'notify_sms_enabled': bool(data.get('notify_sms_enabled', True)),
            'juhe_isbn_key': (data.get('juhe_isbn_key') or '').strip(),
            'bamboo_isbn_apikey': (data.get('bamboo_isbn_apikey') or '').strip(),
            'sms_webhook_url': (data.get('sms_webhook_url') or '').strip(),
            'sms_access_key_id': (data.get('sms_access_key_id') or '').strip(),
            'sms_sign_name': (data.get('sms_sign_name') or '').strip(),
            'sms_template_code': (data.get('sms_template_code') or '').strip(),
            'sms_notify_template_code': (data.get('sms_notify_template_code') or '').strip(),
            'email_webhook_url': (data.get('email_webhook_url') or '').strip(),
        }
    
        # 保存每个设置项
        for key, value in settings_dict.items():
            Setting.set_value(key, value)
    
        # 更新 updated_at
        Setting.set_value('updated_at', time.strftime('%Y-%m-%d %H:%M:%S'))
    
        return jsonify({'status': 'success', 'message': '设置保存成功', 'settings': settings_dict})

