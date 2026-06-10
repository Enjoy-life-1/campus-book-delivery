"""认证与用户 API 路由"""
import os
import random
import re
import time

from flask import jsonify, request, session, redirect

from services.admin_compliance import effective_role, user_ban_blocked
from models import db, User, CampusSchool
from services.phone_code import verify_phone_code as check_phone_code
from app_helpers import sms_channel_configured, sms_using_webhook, SMS_WEBHOOK_HINT
from security import (
    hash_password, verify_password, password_needs_upgrade,
    check_login_rate_limit, record_login_failure, clear_login_attempts,
)


def register_auth_routes(app, helpers):
    """注册登录、注册、用户信息等 API"""
    generate_id = helpers['generate_id']
    is_logged_in = helpers['is_logged_in']
    gateway_url = helpers['gateway_url']
    send_channel_message = helpers['send_channel_message']

    @app.route('/api/health', methods=['GET'])
    def health_check():
        """健康检查，CI/监控用"""
        return jsonify({'status': 'ok', 'message': 'Service is running'})

    @app.route('/api/system/info', methods=['GET'])
    def system_info():
        """系统名称与版本"""
        return jsonify({
            'name': '校园图书配送系统',
            'version': '1.0.0',
            'description': '为校园用户提供图书配送服务的系统',
        })

    @app.route('/api/send_code', methods=['POST'])
    def send_code():
        """发送手机验证码，存入 session['verification_codes']"""
        data = request.json
        phone = data.get('phone', '').strip()
        if not phone or not re.match(r'^1[3-9]\d{9}$', phone):
            return jsonify({'success': False, 'message': '请输入有效的手机号码'}), 400

        sms_on = sms_channel_configured()
        if sms_on:
            code = f'{random.randint(100000, 999999)}'  # 6 位随机码
            status, detail = send_channel_message(
                'sms', phone, '验证码', f'验证码 {code}', '',
                template_params={'code': code},
            )
            if status == 'failed':
                msg = f'短信发送失败：{detail}'
                if sms_using_webhook() and 'Connection refused' in str(detail):
                    msg = 'Webhook 未启动，请先运行「启动短信Webhook.bat」'
                return jsonify({'success': False, 'message': msg}), 502
            if status == 'skipped':
                return jsonify({'success': False, 'message': '短信通道已关闭，请在管理后台开启'}), 503
            hint = SMS_WEBHOOK_HINT if sms_using_webhook() else '验证码已发送至手机'
        elif os.environ.get('FLASK_ENV', '').lower() == 'production':
            return jsonify({'success': False, 'message': '生产环境请配置阿里云短信或 SMS_WEBHOOK_URL'}), 503
        else:
            code = '666666'  # 开发固定测试码
            send_channel_message('sms', phone, '验证码', f'【校园书递】测试验证码 {code}', '')
            hint = f'验证码已发送（测试码：{code}）'

        if 'verification_codes' not in session:
            session['verification_codes'] = {}
        session['verification_codes'][phone] = {
            'code': code,
            'expire_time': time.time() + 300,  # 5 分钟有效
        }
        session.modified = True

        resp = {'success': True, 'message': hint}
        if sms_on and sms_using_webhook():
            resp['webhook_mode'] = True
        if not sms_on:
            resp['code'] = code  # 开发模式返回码方便调试
        return jsonify(resp)

    @app.route('/api/register', methods=['POST'])
    def register():
        """验证码注册新用户"""
        data = request.json
        if not data.get('username') or not data.get('password') or not data.get('phone'):
            return jsonify({'status': 'error', 'message': '请填写完整信息'}), 400

        verify_code = data.get('verifyCode', '').strip()
        phone = data.get('phone', '').strip()
        if not verify_code:
            return jsonify({'status': 'error', 'message': '请输入验证码'}), 400

        ok, msg = check_phone_code(phone, verify_code, session, sms_channel_configured())
        if not ok:
            return jsonify({'status': 'error', 'message': msg}), 400
        verification_codes = session.get('verification_codes', {})

        if User.query.filter_by(username=data['username']).first():
            return jsonify({'status': 'error', 'message': '用户名已存在'}), 400
        if User.query.filter_by(phone=phone).first():
            return jsonify({'status': 'error', 'message': '该手机号已被注册'}), 400

        school_id = (data.get('school_id') or '').strip()
        school_name = ''
        if school_id:
            sch = CampusSchool.query.filter_by(id=school_id, is_active=True).first()
            if sch:
                school_name = sch.name
        new_user = User(
            id=generate_id(),
            username=data['username'],
            password=hash_password(data['password']),
            email=data.get('email', ''),
            phone=phone,
            school=school_name,
            school_id=school_id or None,
            created_at=time.strftime('%Y-%m-%d %H:%M:%S'),
            is_admin=False,
        )
        db.session.add(new_user)
        db.session.commit()

        if phone in verification_codes:
            del verification_codes[phone]
            session['verification_codes'] = verification_codes
            session.modified = True

        return jsonify({'status': 'success', 'message': '注册成功', 'user_id': new_user.id})

    @app.route('/api/login', methods=['POST'])
    def login():
        """普通用户登录，拒绝 admin/moderator"""
        data = request.json or {}
        user_data, err_resp, err_code = _authenticate_user(
            data, staff_only=False, user_only=True,
            is_staff_user=helpers['is_staff_user'],
        )
        if err_resp:
            return err_resp, err_code
        return jsonify({'status': 'success', 'message': '登录成功', 'user': user_data})

    @app.route('/api/admin/login', methods=['POST'])
    def admin_login():
        """管理后台登录，仅 admin/moderator"""
        data = request.json or {}
        user_data, err_resp, err_code = _authenticate_user(
            data, staff_only=True, user_only=False,
            is_staff_user=helpers['is_staff_user'],
        )
        if err_resp:
            return err_resp, err_code
        return jsonify({'status': 'success', 'message': '登录成功', 'user': user_data})

    @app.route('/login')
    def login_page():
        """已登录则跳转，否则返回 Vue 登录页"""
        if 'user_id' in session:
            if session.get('login_portal') == 'admin':
                return redirect('/admin')
            return redirect('/')
        return helpers['serve_vue_or_503']()

    @app.route('/api/logout', methods=['POST'])
    def logout():
        """清除 Session，前端需 refreshSession 或跳转登录"""
        session.clear()  # 清空 Session Cookie
        return jsonify({'status': 'success', 'message': '登出成功'})

    @app.route('/api/user/info', methods=['GET'])
    def get_user_info():
        """前端 refreshSession 调用，Session 为权威登录态"""
        if not is_logged_in():
            return jsonify({'status': 'error', 'message': '请先登录'}), 401
        user = User.query.filter_by(id=str(session['user_id'])).first()
        if not user:
            return jsonify({'status': 'error', 'message': '用户不存在'}), 404
        user_data = user.to_dict()
        from services.book_media import normalize_avatar_url
        user_data['avatar'] = normalize_avatar_url(user_data.get('avatar'))
        user_data['is_admin'] = helpers['is_admin']()
        user_data['login_portal'] = session.get('login_portal') or 'user'
        return jsonify({'status': 'success', 'user': user_data})

    @app.route('/api/user/avatar', methods=['POST'])
    def upload_avatar():
        """上传头像文件 → static/uploads"""
        if not is_logged_in():
            return jsonify({'status': 'error', 'message': '请先登录'}), 401
        f = request.files.get('file')
        if not f or not f.filename:
            return jsonify({'status': 'error', 'message': '请选择图片'}), 400
        ext = f.filename.rsplit('.', 1)[-1].lower() if '.' in f.filename else 'jpg'
        from services.book_media import BOOK_IMAGE_EXT, save_avatar_file
        if ext not in BOOK_IMAGE_EXT:
            return jsonify({'status': 'error', 'message': '仅支持 png/jpg/gif/webp'}), 400
        user = User.query.filter_by(id=str(session['user_id'])).first()
        if not user:
            return jsonify({'status': 'error', 'message': '用户不存在'}), 404
        try:
            url = save_avatar_file(app, f.read(), ext, generate_id)
        except ValueError as e:
            return jsonify({'status': 'error', 'message': str(e)}), 400
        user.avatar = url
        user.updated_at = time.strftime('%Y-%m-%d %H:%M:%S')
        db.session.commit()
        return jsonify({'status': 'success', 'url': url, 'user': user.to_dict()})

    @app.route('/api/user/info', methods=['PUT'])
    def update_user_info():
        """更新个人资料、校区楼栋"""
        if not is_logged_in():
            return jsonify({'status': 'error', 'message': '请先登录'}), 401
        data = request.json
        user = User.query.filter_by(id=str(session['user_id'])).first()
        if not user:
            return jsonify({'status': 'error', 'message': '用户不存在'}), 404

        new_username = data.get('username', '').strip()
        if new_username and new_username != user.username:
            if User.query.filter_by(username=new_username).first():
                return jsonify({'status': 'error', 'message': '用户名已被使用'}), 400

        if 'username' in data:
            user.username = data['username'].strip()
        if 'school' in data:
            user.school = data.get('school', '').strip()
        if 'introduction' in data:
            user.introduction = data.get('introduction', '').strip()
        if 'avatar' in data:
            avatar = (data.get('avatar') or '').strip()
            if avatar.startswith('data:image'):
                from services.book_media import save_avatar_data_url
                try:
                    avatar = save_avatar_data_url(app, avatar, generate_id)
                except ValueError as e:
                    return jsonify({'status': 'error', 'message': str(e)}), 400
            user.avatar = avatar
        if 'email' in data:
            user.email = data.get('email', '').strip()
        if 'phone' in data:
            user.phone = data.get('phone', '').strip()
        from services.campus_dorms import load_dorm_catalog, validate_dorm_zone, dorm_belongs_to_zone
        from models import Setting
        _, by_zone, _ = load_dorm_catalog(Setting)
        if 'campus_zone' in data:
            user.campus_zone = (data.get('campus_zone') or '西校区').strip()
            if user.campus_zone in ('主校区', '生活区'):
                user.campus_zone = '西校区'
            if user.dorm_building and not dorm_belongs_to_zone(user.dorm_building, user.campus_zone, by_zone):
                user.dorm_building = ''
        if 'dorm_building' in data:
            dorm = (data.get('dorm_building') or '').strip()
            zone = (data.get('campus_zone') or user.campus_zone or '西校区').strip()
            ok, msg = validate_dorm_zone(dorm, zone, by_zone)
            if not ok:
                return jsonify({'status': 'error', 'message': msg}), 400
            user.dorm_building = dorm
        if 'notify_email' in data:
            user.notify_email = bool(data.get('notify_email'))
        if 'notify_sms' in data:
            user.notify_sms = bool(data.get('notify_sms'))

        user.updated_at = time.strftime('%Y-%m-%d %H:%M:%S')
        db.session.commit()
        if 'username' in data:
            session['username'] = data['username'].strip()
        return jsonify({'status': 'success', 'message': '信息更新成功', 'user': user.to_dict()})

    @app.route('/api/user/password', methods=['PUT'])
    def change_password():
        """修改密码；verify 旧密码后 hash 新密码"""
        if not is_logged_in():
            return jsonify({'status': 'error', 'message': '请先登录'}), 401
        data = request.json
        old_password = data.get('oldPassword', '').strip()
        new_password = data.get('newPassword', '').strip()
        confirm_password = data.get('confirmPassword', '').strip()
        if not old_password or not new_password or not confirm_password:
            return jsonify({'status': 'error', 'message': '请填写所有密码字段'}), 400
        if new_password != confirm_password:
            return jsonify({'status': 'error', 'message': '两次输入的新密码不一致'}), 400
        if len(new_password) < 6:
            return jsonify({'status': 'error', 'message': '密码长度不能少于6位'}), 400
        user = User.query.filter_by(id=str(session['user_id'])).first()
        if not user:
            return jsonify({'status': 'error', 'message': '用户不存在'}), 404
        if not verify_password(old_password, user.password):
            return jsonify({'status': 'error', 'message': '当前密码不正确'}), 400
        user.password = hash_password(new_password)
        user.updated_at = time.strftime('%Y-%m-%d %H:%M:%S')
        db.session.commit()
        return jsonify({'status': 'success', 'message': '密码修改成功'})

    return {
        'health_check': health_check,
        'login': login,
        'logout': logout,
        'get_user_info': get_user_info,
    }


def _authenticate_user(data, staff_only=False, user_only=False, is_staff_user=None):
    """校验账号密码，写入 session，返回 (user_data, err_resp, err_code)"""
    username = (data.get('username') or '').strip()
    if not check_login_rate_limit(username):
        return None, jsonify({'status': 'error', 'message': '登录尝试过多，请5分钟后再试'}), 429

    raw_password = data.get('password', '')
    cleaned_password = raw_password.strip()
    if (cleaned_password.startswith('\'') and cleaned_password.endswith('\'')) or \
       (cleaned_password.startswith('"') and cleaned_password.endswith('"')):
        cleaned_password = cleaned_password[1:-1].strip()

    user = User.query.filter_by(username=username).first()
    if not user or not verify_password(cleaned_password, user.password):
        record_login_failure(username)
        return None, jsonify({'status': 'error', 'message': '账号或密码错误'}), 401

    if password_needs_upgrade(user.password):
        user.password = hash_password(cleaned_password)  # MD5 → pbkdf2 升级
        db.session.commit()

    ban_msg = user_ban_blocked(user)
    if ban_msg:
        return None, jsonify({'status': 'error', 'message': ban_msg}), 403

    role = effective_role(user)
    if staff_only and role not in ('admin', 'moderator'):
        record_login_failure(username)
        return None, jsonify({'status': 'error', 'message': '账号或密码错误'}), 401
    if user_only and role in ('admin', 'moderator'):
        record_login_failure(username)
        return None, jsonify({'status': 'error', 'message': '管理员请使用管理后台登录入口'}), 403

    is_admin_user = role in ('admin', 'moderator')
    clear_login_attempts(username)
    session['user_id'] = user.id  # ★ 写入 Session
    session['username'] = user.username
    session['login_portal'] = 'admin' if staff_only else 'user'
    session['is_admin'] = is_admin_user if staff_only else False
    session['role'] = role
    user_data = user.to_dict()
    user_data['is_admin'] = is_admin_user
    user_data['role'] = role
    return user_data, None, None
