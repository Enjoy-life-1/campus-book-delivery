"""管理端合规：敏感词、操作日志、ISBN 黑名单、封禁申诉、周期报表、角色分权"""
import csv
import re
import time
from datetime import datetime, timedelta
from io import StringIO

from flask import request, jsonify, session, Response

from models import (
    db, User, Book, Order, Comment, SensitiveWord, AdminAuditLog,
    IsbnBlacklist, BanAppeal, Setting
)


def _gid():
    """生成毫秒时间戳 + 随机后缀 ID"""
    import random
    return f'{int(time.time() * 1000)}{random.randint(100, 999)}'


def _now():
    """当前时间字符串"""
    return time.strftime('%Y-%m-%d %H:%M:%S')


def _parse_dt(s):
    """解析 YYYY-MM-DD HH:MM:SS 前缀"""
    if not s:
        return None
    try:
        return datetime.strptime(s[:19], '%Y-%m-%d %H:%M:%S')
    except ValueError:
        return None


def effective_role(user):
    """student / moderator / admin"""
    if not user:
        return 'student'
    if user.is_admin:
        return 'admin'
    return user.role or 'student'


def is_staff_user(user):
    """admin 或 moderator"""
    return effective_role(user) in ('admin', 'moderator')


def is_full_admin_user(user):
    """仅超级管理员"""
    return effective_role(user) == 'admin'


def user_ban_blocked(user):
    """登录/发书等：封禁检查"""
    if not user:
        return None
    lvl = user.ban_level or 'none'
    if lvl != 'ban':
        return None
    until = _parse_dt(user.ban_until)
    if until and until < datetime.now():
        user.ban_level = 'none'
        user.ban_until = None
        user.ban_reason = None
        db.session.commit()
        return None
    reason = user.ban_reason or '违反平台规则'
    return f'账号已封禁：{reason}' + (f'（至 {user.ban_until}）' if user.ban_until else '')


def user_mute_blocked(user):
    """私信发送前：mute/ban 检查"""
    if not user:
        return None
    if (user.ban_level or 'none') not in ('mute', 'ban'):
        return None
    if user.ban_level == 'ban':
        return user_ban_blocked(user)
    until = _parse_dt(user.ban_until)
    if until and until < datetime.now():
        user.ban_level = 'none'
        user.ban_until = None
        db.session.commit()
        return None
    return '您已被禁言，暂无法发送私信'


def log_admin(action, target_type='', target_id='', detail=''):
    """写入 AdminAuditLog；仅 staff 操作记录"""
    if 'user_id' not in session:
        return
    admin = User.query.filter_by(id=str(session['user_id'])).first()
    if not admin or not is_staff_user(admin):
        return
    db.session.add(AdminAuditLog(
        id=_gid(),
        admin_id=str(admin.id),
        admin_name=admin.username,
        action=action,
        target_type=target_type or '',
        target_id=str(target_id or ''),
        detail=(detail or '')[:1000],
        ip=(request.remote_addr or '')[:50],
        created_at=_now()
    ))


def match_sensitive(text, scope='all'):
    """子串匹配敏感词；scope: all/comment/message 等"""
    if not text:
        return None
    low = text.lower()
    q = SensitiveWord.query.filter_by(is_active=True)
    if scope != 'all':
        q = q.filter(db.or_(SensitiveWord.scope == 'all', SensitiveWord.scope == scope))
    for row in q.all():
        w = (row.word or '').strip().lower()
        if w and w in low:
            return row.word
    return None


def isbn_blacklisted(isbn):
    """发布前 ISBN 黑名单校验"""
    clean = re.sub(r'[^0-9Xx]', '', isbn or '')
    if not clean:
        return None
    row = IsbnBlacklist.query.filter_by(isbn=clean).first()
    return row


def register_compliance_routes(app, helpers):
    """合规 API：敏感词/审计/ISBN 黑名单/封禁申诉/周期报表"""
    is_logged_in = helpers['is_logged_in']
    is_admin_fn = helpers.get('is_admin')
    is_full_admin_fn = helpers.get('is_full_admin')

    def current_user():
        if not is_logged_in():
            return None
        return User.query.filter_by(id=str(session['user_id'])).first()

    def require_staff():
        if is_admin_fn and not is_admin_fn():
            return None, (jsonify({'status': 'error', 'message': '无管理权限'}), 403)
        u = current_user()
        if not u:
            return None, (jsonify({'status': 'error', 'message': '无管理权限'}), 403)
        return u, None

    def require_admin():
        if is_full_admin_fn and not is_full_admin_fn():
            return None, (jsonify({'status': 'error', 'message': '需要超级管理员权限'}), 403)
        u = current_user()
        if not u or not is_full_admin_user(u):
            return None, (jsonify({'status': 'error', 'message': '需要超级管理员权限'}), 403)
        return u, None

    @app.after_request
    def auto_audit_admin(response):
        """管理端 POST/PUT/DELETE 自动记审计日志"""
        if request.method in ('POST', 'PUT', 'DELETE') and request.path.startswith('/api/admin/'):
            if is_logged_in():
                try:
                    log_admin(
                        f'{request.method} {request.path}',
                        'api',
                        '',
                        (request.get_data(as_text=True) or '')[:500]
                    )
                    db.session.commit()
                except Exception:
                    db.session.rollback()
        return response

    # ---------- 敏感词 ----------
    @app.route('/api/admin/sensitive-words', methods=['GET'])
    def list_sensitive_words():
        """敏感词列表"""
        _, err = require_staff()
        if err:
            return err
        rows = SensitiveWord.query.order_by(SensitiveWord.created_at.desc()).all()
        return jsonify({'status': 'success', 'words': [r.to_dict() for r in rows]})

    @app.route('/api/admin/sensitive-words', methods=['POST'])
    def add_sensitive_word():
        """新增敏感词"""
        _, err = require_staff()
        if err:
            return err
        data = request.json or {}
        word = (data.get('word') or '').strip()
        if not word:
            return jsonify({'status': 'error', 'message': '敏感词不能为空'}), 400
        scope = (data.get('scope') or 'all').strip()
        row = SensitiveWord(
            id=_gid(), word=word, scope=scope, is_active=True, created_at=_now()
        )
        db.session.add(row)
        db.session.commit()
        return jsonify({'status': 'success', 'word': row.to_dict()})

    @app.route('/api/admin/sensitive-words/<wid>', methods=['DELETE'])
    def delete_sensitive_word(wid):
        """删除敏感词"""
        _, err = require_staff()
        if err:
            return err
        row = SensitiveWord.query.filter_by(id=str(wid)).first()
        if row:
            db.session.delete(row)
            db.session.commit()
        return jsonify({'status': 'success'})

    # ---------- 操作日志 ----------
    @app.route('/api/admin/audit-logs', methods=['GET'])
    def list_audit_logs():
        """管理员操作审计日志"""
        _, err = require_admin()
        if err:
            return err
        limit = min(int(request.args.get('limit', 200)), 500)
        rows = AdminAuditLog.query.order_by(AdminAuditLog.created_at.desc()).limit(limit).all()
        return jsonify({'status': 'success', 'logs': [r.to_dict() for r in rows]})

    # ---------- ISBN 黑名单 ----------
    @app.route('/api/admin/isbn-blacklist', methods=['GET'])
    def list_isbn_blacklist():
        """ISBN 黑名单列表"""
        _, err = require_staff()
        if err:
            return err
        rows = IsbnBlacklist.query.order_by(IsbnBlacklist.created_at.desc()).all()
        return jsonify({'status': 'success', 'items': [r.to_dict() for r in rows]})

    @app.route('/api/admin/isbn-blacklist', methods=['POST'])
    def add_isbn_blacklist():
        """加入 ISBN 黑名单"""
        _, err = require_staff()
        if err:
            return err
        data = request.json or {}
        isbn = re.sub(r'[^0-9Xx]', '', data.get('isbn') or '')
        if len(isbn) < 10:
            return jsonify({'status': 'error', 'message': 'ISBN 格式不正确'}), 400
        if IsbnBlacklist.query.filter_by(isbn=isbn).first():
            return jsonify({'status': 'error', 'message': '已在黑名单中'}), 400
        row = IsbnBlacklist(
            id=_gid(), isbn=isbn, reason=(data.get('reason') or '').strip(), created_at=_now()
        )
        db.session.add(row)
        db.session.commit()
        return jsonify({'status': 'success', 'item': row.to_dict()})

    @app.route('/api/admin/isbn-blacklist/<bid>', methods=['DELETE'])
    def delete_isbn_blacklist(bid):
        """移出 ISBN 黑名单"""
        _, err = require_staff()
        if err:
            return err
        row = IsbnBlacklist.query.filter_by(id=str(bid)).first()
        if row:
            db.session.delete(row)
            db.session.commit()
        return jsonify({'status': 'success'})

    # ---------- 封禁 ----------
    @app.route('/api/admin/users/<user_id>/ban', methods=['POST'])
    def ban_user(user_id):
        """warning / mute / ban；可设 days 到期"""
        admin, err = require_admin()
        if err:
            return err
        data = request.json or {}
        level = (data.get('level') or 'mute').strip()
        if level not in ('warning', 'mute', 'ban'):
            return jsonify({'status': 'error', 'message': 'level 须为 warning/mute/ban'}), 400
        days = int(data.get('days', 7) or 0)
        reason = (data.get('reason') or '违反平台规则').strip()
        user = User.query.filter_by(id=str(user_id)).first()
        if not user:
            return jsonify({'status': 'error', 'message': '用户不存在'}), 404
        if str(user.id) == str(admin.id):
            return jsonify({'status': 'error', 'message': '不能封禁自己'}), 400
        user.ban_level = level
        user.ban_reason = reason
        if level == 'warning':
            user.ban_until = None
        elif days > 0:
            user.ban_until = (datetime.now() + timedelta(days=days)).strftime('%Y-%m-%d %H:%M:%S')
        else:
            user.ban_until = None
        db.session.commit()
        log_admin('ban_user', 'user', user_id, f'{level} {days}d {reason}')
        db.session.commit()
        return jsonify({'status': 'success', 'user': user.to_dict()})

    @app.route('/api/admin/users/<user_id>/unban', methods=['POST'])
    def unban_user(user_id):
        """解除封禁/禁言"""
        _, err = require_admin()
        if err:
            return err
        user = User.query.filter_by(id=str(user_id)).first()
        if not user:
            return jsonify({'status': 'error', 'message': '用户不存在'}), 404
        user.ban_level = 'none'
        user.ban_until = None
        user.ban_reason = None
        db.session.commit()
        log_admin('unban_user', 'user', user_id, '')
        db.session.commit()
        return jsonify({'status': 'success', 'user': user.to_dict()})

    # ---------- 申诉 ----------
    @app.route('/api/ban-appeal', methods=['POST'])
    def submit_ban_appeal():
        """用户提交封禁申诉"""
        if not is_logged_in():
            return jsonify({'status': 'error', 'message': '请先登录'}), 401
        user = current_user()
        if (user.ban_level or 'none') not in ('mute', 'ban'):
            return jsonify({'status': 'error', 'message': '当前账号无需申诉'}), 400
        content = (request.json or {}).get('content', '').strip()
        if len(content) < 10:
            return jsonify({'status': 'error', 'message': '申诉说明至少10字'}), 400
        pending = BanAppeal.query.filter_by(user_id=str(user.id), status='pending').first()
        if pending:
            return jsonify({'status': 'error', 'message': '已有待处理申诉'}), 400
        row = BanAppeal(
            id=_gid(),
            user_id=str(user.id),
            username=user.username,
            ban_level=user.ban_level,
            content=content,
            status='pending',
            created_at=_now(),
            updated_at=_now()
        )
        db.session.add(row)
        db.session.commit()
        return jsonify({'status': 'success', 'appeal': row.to_dict()})

    @app.route('/api/ban-appeal/mine', methods=['GET'])
    def my_ban_appeals():
        """我的封禁申诉记录"""
        if not is_logged_in():
            return jsonify({'status': 'error', 'message': '请先登录'}), 401
        rows = BanAppeal.query.filter_by(user_id=str(session['user_id'])).order_by(
            BanAppeal.created_at.desc()
        ).limit(20).all()
        return jsonify({'status': 'success', 'appeals': [r.to_dict() for r in rows]})

    @app.route('/api/admin/ban-appeals', methods=['GET'])
    def list_ban_appeals():
        """封禁申诉列表（可按 status 筛选）"""
        _, err = require_staff()
        if err:
            return err
        st = (request.args.get('status') or '').strip()
        q = BanAppeal.query
        if st:
            q = q.filter_by(status=st)
        rows = q.order_by(BanAppeal.created_at.desc()).limit(200).all()
        return jsonify({'status': 'success', 'appeals': [r.to_dict() for r in rows]})

    @app.route('/api/admin/ban-appeals/<aid>', methods=['PUT'])
    def handle_ban_appeal(aid):
        """审批申诉；approved 时自动解封"""
        admin, err = require_staff()
        if err:
            return err
        row = BanAppeal.query.filter_by(id=str(aid)).first()
        if not row:
            return jsonify({'status': 'error', 'message': '申诉不存在'}), 404
        data = request.json or {}
        status = (data.get('status') or '').strip()
        if status not in ('approved', 'rejected'):
            return jsonify({'status': 'error', 'message': 'status 须为 approved/rejected'}), 400
        row.status = status
        row.admin_reply = (data.get('admin_reply') or '').strip()
        row.handled_by = str(admin.id)
        row.updated_at = _now()
        user = User.query.filter_by(id=str(row.user_id)).first()
        if user and status == 'approved':
            user.ban_level = 'none'
            user.ban_until = None
            user.ban_reason = None
        db.session.commit()
        return jsonify({'status': 'success', 'appeal': row.to_dict()})

    # ---------- 周期报表 ----------
    @app.route('/api/admin/reports/periodic', methods=['GET'])
    def export_periodic_report():
        """导出近 7/30 天运营 CSV"""
        _, err = require_admin()
        if err:
            return err
        period = (request.args.get('period') or 'week').strip()
        days = 30 if period == 'month' else 7
        since = datetime.now() - timedelta(days=days)
        since_s = since.strftime('%Y-%m-%d %H:%M:%S')

        orders = Order.query.all()
        books = Book.query.all()
        users = User.query.all()

        def in_range(ts):
            dt = _parse_dt(ts)
            return dt and dt >= since

        recent_orders = [o for o in orders if in_range(o.created_at)]
        recent_books = [b for b in books if in_range(b.created_at)]
        recent_users = [u for u in users if in_range(u.created_at)]

        si = StringIO()
        w = csv.writer(si)
        w.writerow(['校园书递周期运营报表'])
        w.writerow(['统计周期', f'近{days}天', '自', since_s])
        w.writerow([])
        w.writerow(['指标', '数值'])
        w.writerow(['新增用户', len(recent_users)])
        w.writerow(['新增书籍', len(recent_books)])
        w.writerow(['新增订单', len(recent_orders)])
        completed = sum(1 for o in recent_orders if o.status == 'completed')
        w.writerow(['完成订单', completed])
        sales = sum(float(o.price or 0) for o in recent_orders if o.status == 'completed' and (o.order_type or 'sale') != 'exchange')
        w.writerow(['成交额', f'{sales:.2f}'])
        w.writerow(['待审书籍', sum(1 for b in books if b.status == 'pending')])
        w.writerow(['待审评论', Comment.query.filter_by(audit_status='pending', is_deleted=False).count()])
        w.writerow([])
        w.writerow(['订单明细'])
        w.writerow(['订单号', '类型', '书名', '金额', '状态', '时间'])
        for o in recent_orders:
            w.writerow([
                o.id, o.order_type or 'sale', o.book_title or '',
                o.price or '', o.status or '', o.created_at or ''
            ])
        fname = f'report_{period}_{datetime.now().strftime("%Y%m%d")}.csv'
        return Response(
            '\ufeff' + si.getvalue(),
            mimetype='text/csv; charset=utf-8',
            headers={'Content-Disposition': f'attachment; filename={fname}'}
        )


def seed_compliance_data(_db, SensitiveWordModel, IsbnBlacklistModel):
    """初始化默认敏感词与示例 ISBN 黑名单"""
    ts = _now()
    defaults = [
        ('盗版', 'all'), ('违禁', 'all'), ('黄赌毒', 'all'),
        ('枪支', 'all'), ('色情', 'all'), ('刷单', 'all'),
    ]
    for word, scope in defaults:
        if not SensitiveWordModel.query.filter_by(word=word).first():
            _db.session.add(SensitiveWordModel(
                id=_gid(), word=word, scope=scope, is_active=True, created_at=ts
            ))
    if not IsbnBlacklistModel.query.first():
        _db.session.add(IsbnBlacklistModel(
            id=_gid(), isbn='9780000000000', reason='示例黑名单ISBN（测试）', created_at=ts
        ))
