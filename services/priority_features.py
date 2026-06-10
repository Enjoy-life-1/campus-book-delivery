"""高/中优先级功能 API"""
import json
import os
import re
import time
import urllib.request
import urllib.parse

from flask import jsonify, request, session

from models import (
    db, User, Book, Order, Comment, Setting,
    CampusSchool, UserBlock, Report
)
from security import hash_password, verify_password, password_needs_upgrade


def _gid():
    from app import generate_id
    return generate_id()


def _logged_in():
    from app import is_logged_in
    return is_logged_in()


def _admin():
    from app import is_admin
    return is_admin()


def _push(user_id, ntype, title, content='', link=''):
    from app import push_notification
    push_notification(user_id, ntype, title, content, link)


def _blocked_ids(uid):
    rows = UserBlock.query.filter_by(blocker_id=str(uid)).all()
    return {r.blocked_id for r in rows}


def _email_domain_ok(email, school):
    if not email or '@' not in email:
        return False
    domain = email.split('@', 1)[1].lower().strip()
    for d in school.domain_list():
        d = (d or '').lower().strip().lstrip('@')
        if domain == d or domain.endswith('.' + d) or domain.endswith(d):
            return True
    return False


def register_priority_routes(app):
    """学校列表、忘记密码、学籍认证、举报拉黑、换书、评论审核"""
    @app.route('/api/schools', methods=['GET'])
    def list_schools():
        """注册/认证页可选学校列表"""
        rows = CampusSchool.query.filter_by(is_active=True).order_by(CampusSchool.sort_order).all()
        return jsonify({'status': 'success', 'schools': [s.to_dict() for s in rows]})

    @app.route('/api/forgot-password', methods=['POST'])
    def forgot_password_reset():
        """短信验证码重置密码"""
        data = request.json or {}
        phone = (data.get('phone') or '').strip()
        code = (data.get('code') or '').strip()
        new_password = (data.get('new_password') or '').strip()
        if not re.match(r'^1[3-9]\d{9}$', phone):
            return jsonify({'status': 'error', 'message': '手机号格式不正确'}), 400
        if not new_password or len(new_password) < 6:
            return jsonify({'status': 'error', 'message': '新密码至少6位'}), 400
        from .phone_code import verify_phone_code
        from app_helpers import sms_channel_configured
        ok, msg = verify_phone_code(phone, code, session, sms_channel_configured())
        if not ok:
            return jsonify({'status': 'error', 'message': msg}), 400
        user = User.query.filter_by(phone=phone).first()
        if not user:
            return jsonify({'status': 'error', 'message': '该手机号未注册'}), 404
        user.password = hash_password(new_password)
        user.updated_at = time.strftime('%Y-%m-%d %H:%M:%S')
        db.session.commit()
        return jsonify({'status': 'success', 'message': '密码已重置，请登录'})

    @app.route('/api/campus/verify', methods=['POST'])
    def campus_verify():
        """AccountSettings 学籍认证：校验校园邮箱后缀"""
        if not _logged_in():
            return jsonify({'status': 'error', 'message': '请先登录'}), 401
        data = request.json or {}
        campus_email = (data.get('campus_email') or data.get('email') or '').strip().lower()
        student_id = (data.get('student_id') or '').strip()
        school_id = (data.get('school_id') or '').strip()
        user = User.query.filter_by(id=str(session['user_id'])).first()
        if not user:
            return jsonify({'status': 'error', 'message': '用户不存在'}), 404
        school = None
        if school_id:
            school = CampusSchool.query.filter_by(id=school_id, is_active=True).first()
        if not school and user.school_id:
            school = CampusSchool.query.filter_by(id=user.school_id).first()
        if not school:
            school = CampusSchool.query.filter_by(is_active=True).order_by(CampusSchool.sort_order).first()
        if not school:
            return jsonify({'status': 'error', 'message': '暂未配置学校，请联系管理员'}), 400
        if not campus_email or not _email_domain_ok(campus_email, school):
            domains = '、'.join(school.domain_list()) or '学校邮箱后缀'
            return jsonify({'status': 'error', 'message': f'请使用本校邮箱（{domains}）'}), 400
        user.campus_email = campus_email
        user.student_id = student_id or user.student_id
        user.school_id = school.id
        user.school = school.name
        user.campus_verified = True
        user.updated_at = time.strftime('%Y-%m-%d %H:%M:%S')
        db.session.commit()
        return jsonify({'status': 'success', 'message': '学籍认证成功', 'user': user.to_dict()})

    @app.route('/api/reports', methods=['POST'])
    def create_report():
        """举报用户/书籍/评论"""
        if not _logged_in():
            return jsonify({'status': 'error', 'message': '请先登录'}), 401
        data = request.json or {}
        target_type = (data.get('target_type') or '').strip()
        target_id = str(data.get('target_id') or '').strip()
        reason = (data.get('reason') or '').strip()
        if target_type not in ('user', 'book', 'comment'):
            return jsonify({'status': 'error', 'message': '举报类型无效'}), 400
        if not target_id or not reason:
            return jsonify({'status': 'error', 'message': '请填写举报对象与原因'}), 400
        r = Report(
            id=_gid(),
            reporter_id=str(session['user_id']),
            reporter_name=session.get('username', ''),
            target_type=target_type,
            target_id=target_id,
            reason=reason[:500],
            status='pending',
            created_at=time.strftime('%Y-%m-%d %H:%M:%S')
        )
        db.session.add(r)
        db.session.commit()
        return jsonify({'status': 'success', 'message': '举报已提交，管理员将处理'})

    @app.route('/api/block/<user_id>', methods=['POST'])
    def block_user(user_id):
        """拉黑用户"""
        if not _logged_in():
            return jsonify({'status': 'error', 'message': '请先登录'}), 401
        uid = str(session['user_id'])
        bid = str(user_id)
        if uid == bid:
            return jsonify({'status': 'error', 'message': '不能拉黑自己'}), 400
        if not UserBlock.query.filter_by(blocker_id=uid, blocked_id=bid).first():
            db.session.add(UserBlock(
                id=_gid(), blocker_id=uid, blocked_id=bid,
                created_at=time.strftime('%Y-%m-%d %H:%M:%S')
            ))
            db.session.commit()
        return jsonify({'status': 'success', 'message': '已拉黑'})

    @app.route('/api/block/<user_id>', methods=['DELETE'])
    def unblock_user(user_id):
        """取消拉黑"""
        if not _logged_in():
            return jsonify({'status': 'error', 'message': '请先登录'}), 401
        UserBlock.query.filter_by(
            blocker_id=str(session['user_id']), blocked_id=str(user_id)
        ).delete()
        db.session.commit()
        return jsonify({'status': 'success', 'message': '已取消拉黑'})

    @app.route('/api/block/list', methods=['GET'])
    def block_list():
        """当前用户拉黑列表"""
        if not _logged_in():
            return jsonify({'status': 'error', 'message': '请先登录'}), 401
        ids = list(_blocked_ids(session['user_id']))
        users = User.query.filter(User.id.in_(ids)).all() if ids else []
        return jsonify({
            'status': 'success',
            'blocked': [{'id': u.id, 'username': u.username} for u in users]
        })

    @app.route('/api/orders/exchange', methods=['POST'])
    def create_exchange_order():
        """BookDetail 换书申请 order_type=exchange"""
        if not _logged_in():
            return jsonify({'status': 'error', 'message': '请先登录'}), 401
        data = request.json or {}
        book = Book.query.filter_by(id=str(data.get('book_id', ''))).first()
        if not book:
            return jsonify({'status': 'error', 'message': '书籍不存在'}), 404
        if book.status != 'available':
            return jsonify({'status': 'error', 'message': '书籍不可换'}), 400
        owner_id = str(book.owner_id or book.sellerId or '')
        if owner_id == str(session['user_id']):
            return jsonify({'status': 'error', 'message': '不能换自己的书'}), 400
        title = (data.get('exchange_book_title') or '').strip()
        if not title:
            return jsonify({'status': 'error', 'message': '请填写用于交换的书名'}), 400
        order = Order(
            id=_gid(),
            book_id=str(book.id),
            book_title=book.title,
            buyer_id=str(session['user_id']),
            buyer_name=session.get('username', ''),
            seller_id=owner_id,
            seller_name=book.owner_name or book.seller or '',
            price=0.0,
            status='pending',
            order_type='exchange',
            exchange_book_title=title,
            exchange_note=(data.get('exchange_note') or '').strip(),
            created_at=time.strftime('%Y-%m-%d %H:%M:%S')
        )
        db.session.add(order)
        _push(owner_id, 'order', '收到换书请求',
              f'{session.get("username")} 想用《{title}》换您的《{book.title}》',
              f'/order/{order.id}')
        db.session.commit()
        return jsonify({'status': 'success', 'message': '换书申请已提交', 'order': order.to_dict()})

    @app.route('/api/admin/comments/pending', methods=['GET'])
    def admin_pending_comments():
        if not _admin():
            return jsonify({'status': 'error', 'message': '需要管理员权限'}), 403
        rows = Comment.query.filter_by(audit_status='pending', is_deleted=False).order_by(
            Comment.created_at.desc()
        ).all()
        return jsonify({'status': 'success', 'comments': [c.to_dict() for c in rows]})

    @app.route('/api/admin/comments/<comment_id>/audit', methods=['PUT'])
    def admin_audit_comment(comment_id):
        """通过/拒绝 pending 评论并通知"""
        if not _admin():
            return jsonify({'status': 'error', 'message': '需要管理员权限'}), 403
        data = request.json or {}
        st = (data.get('status') or '').strip()
        if st not in ('approved', 'rejected'):
            return jsonify({'status': 'error', 'message': '状态无效'}), 400
        c = Comment.query.filter_by(id=str(comment_id)).first()
        if not c:
            return jsonify({'status': 'error', 'message': '评论不存在'}), 404
        c.audit_status = st
        if st == 'rejected':
            c.is_deleted = True
        elif st == 'approved':
            _push(c.user_id, 'audit', '您的评论已通过审核',
                  f'《{c.book_title}》下的评论已展示', f'/book/{c.book_id}')
            book = Book.query.filter_by(id=c.book_id).first()
            if book and str(book.owner_id) != str(c.user_id):
                _push(book.owner_id, 'comment', '书籍收到新评论',
                      f'《{c.book_title}》有新评论', f'/book/{c.book_id}')
        db.session.commit()
        return jsonify({'status': 'success', 'message': '已处理'})

    @app.route('/api/admin/reports', methods=['GET'])
    def admin_reports():
        if not _admin():
            return jsonify({'status': 'error', 'message': '需要管理员权限'}), 403
        status = request.args.get('status', 'pending')
        q = Report.query
        if status != 'all':
            q = q.filter_by(status=status)
        rows = q.order_by(Report.created_at.desc()).limit(200).all()
        return jsonify({'status': 'success', 'reports': [r.to_dict() for r in rows]})

    @app.route('/api/admin/reports/<rid>', methods=['PUT'])
    def admin_handle_report(rid):
        if not _admin():
            return jsonify({'status': 'error', 'message': '需要管理员权限'}), 403
        data = request.json or {}
        r = Report.query.filter_by(id=str(rid)).first()
        if not r:
            return jsonify({'status': 'error', 'message': '记录不存在'}), 404
        r.status = (data.get('status') or 'handled').strip()
        r.admin_note = (data.get('admin_note') or '').strip()
        db.session.commit()
        return jsonify({'status': 'success', 'message': '已更新'})

    @app.route('/api/admin/schools', methods=['GET'])
    def admin_schools():
        if not _admin():
            return jsonify({'status': 'error', 'message': '需要管理员权限'}), 403
        rows = CampusSchool.query.order_by(CampusSchool.sort_order).all()
        return jsonify({'status': 'success', 'schools': [s.to_dict() for s in rows]})

    @app.route('/api/admin/schools', methods=['POST'])
    def admin_create_school():
        if not _admin():
            return jsonify({'status': 'error', 'message': '需要管理员权限'}), 403
        data = request.json or {}
        name = (data.get('name') or '').strip()
        if not name:
            return jsonify({'status': 'error', 'message': '学校名称必填'}), 400
        domains = data.get('email_domains') or []
        if isinstance(domains, str):
            domains = [x.strip() for x in domains.split(',') if x.strip()]
        s = CampusSchool(
            id=_gid(),
            name=name,
            email_domains=json.dumps(domains, ensure_ascii=False),
            is_active=data.get('is_active', True) is not False,
            sort_order=int(data.get('sort_order') or 0),
            created_at=time.strftime('%Y-%m-%d %H:%M:%S')
        )
        db.session.add(s)
        db.session.commit()
        return jsonify({'status': 'success', 'school': s.to_dict()})

    @app.route('/api/admin/schools/<sid>', methods=['PUT'])
    def admin_update_school(sid):
        if not _admin():
            return jsonify({'status': 'error', 'message': '需要管理员权限'}), 403
        s = CampusSchool.query.filter_by(id=str(sid)).first()
        if not s:
            return jsonify({'status': 'error', 'message': '学校不存在'}), 404
        data = request.json or {}
        if 'name' in data:
            s.name = (data['name'] or '').strip()
        if 'email_domains' in data:
            domains = data['email_domains']
            if isinstance(domains, str):
                domains = [x.strip() for x in domains.split(',') if x.strip()]
            s.email_domains = json.dumps(domains, ensure_ascii=False)
        if 'is_active' in data:
            s.is_active = bool(data['is_active'])
        if 'sort_order' in data:
            s.sort_order = int(data['sort_order'] or 0)
        db.session.commit()
        return jsonify({'status': 'success', 'school': s.to_dict()})

    @app.route('/api/admin/schools/<sid>', methods=['DELETE'])
    def admin_delete_school(sid):
        if not _admin():
            return jsonify({'status': 'error', 'message': '需要管理员权限'}), 403
        CampusSchool.query.filter_by(id=str(sid)).delete()
        db.session.commit()
        return jsonify({'status': 'success', 'message': '已删除'})
