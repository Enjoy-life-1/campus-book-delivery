"""卖家工具：浏览统计、发布模板、套装、阶梯降价、降价订阅、公开分享"""
import json
import random
import time
from datetime import datetime, timedelta

from flask import request, jsonify, session

from models import (
    db, User, Book, Order, Collection, BookView, PublishTemplate, WantedPost
)


def _gid():
    return f'{int(time.time() * 1000)}{random.randint(100, 999)}'


def _now():
    return time.strftime('%Y-%m-%d %H:%M:%S')


def record_book_view(book_id, viewer_id=None):
    """详情页浏览 +1；写入 BookView 供个性化推荐"""
    book = Book.query.filter_by(id=str(book_id)).first()
    if not book:
        return
    if viewer_id and str(viewer_id) == str(book.owner_id or ''):
        return
    book.view_count = int(book.view_count or 0) + 1
    db.session.add(BookView(
        id=_gid(),
        book_id=str(book_id),
        user_id=str(viewer_id or ''),
        created_at=_now()
    ))
    db.session.commit()


def seller_view_metrics(user_id):
    uid = str(user_id)
    books = Book.query.filter_by(owner_id=uid).all()
    total_views = sum(int(b.view_count or 0) for b in books)
    completed = Order.query.filter_by(seller_id=uid, status='completed').count()
    conversion = round((completed / total_views * 100), 1) if total_views else 0.0
    return {'total_views': total_views, 'conversion_rate': conversion}


def apply_price_drop_ladders(notify_fn=None):
    """按阶梯计划自动降价"""
    now = datetime.now()
    changed = []
    for book in Book.query.filter_by(status='available').all():
        plan = Book._json_load(book.price_drop_plan)
        if not plan or plan.get('mode') != 'ladder':
            continue
        started = plan.get('started_at', '')
        try:
            start_dt = datetime.strptime(started[:19], '%Y-%m-%d %H:%M:%S')
        except (ValueError, TypeError):
            continue
        elapsed_h = (now - start_dt).total_seconds() / 3600
        steps = sorted(plan.get('steps') or [], key=lambda x: x.get('hours', 0))
        target = None
        for st in steps:
            if elapsed_h >= float(st.get('hours', 0)):
                target = float(st.get('price', 0))
        if target is None or target <= 0:
            continue
        if float(book.price or 0) <= target:
            continue
        old = float(book.price)
        if not book.original_price:
            book.original_price = old
        book.price = target
        book.updated_at = _now()
        last_h = steps[-1].get('hours', 72) if steps else 72
        book.price_drop_until = (start_dt + timedelta(hours=float(last_h))).strftime('%Y-%m-%d %H:%M:%S')
        changed.append(book)
        if notify_fn:
            notify_fn(book, old)
    if changed:
        db.session.commit()
    return len(changed)


def register_seller_tools(app, helpers):
    """卖家仪表盘、发布模板、降价订阅、公开分享 API"""
    is_logged_in = helpers['is_logged_in']
    generate_id = helpers['generate_id']
    enrich_book_dict = helpers.get('enrich_book_dict')
    notify_price_drop = helpers.get('notify_price_drop')
    find_wanted_matches = helpers.get('find_wanted_matches')

    @app.route('/api/seller/dashboard', methods=['GET'])
    def seller_dashboard():
        """PersonalCenter 卖家数据卡片"""
        if not is_logged_in():
            return jsonify({'status': 'error', 'message': '请先登录'}), 401
        uid = str(session['user_id'])
        stats = helpers['seller_profile_stats'](uid)
        stats.update(seller_view_metrics(uid))
        books = Book.query.filter_by(owner_id=uid, status='available').limit(12).all()
        return jsonify({
            'status': 'success',
            'stats': stats,
            'books': [b.to_dict() for b in books]
        })

    @app.route('/api/my/publish-templates', methods=['GET'])
    def list_templates():
        if not is_logged_in():
            return jsonify({'status': 'error', 'message': '请先登录'}), 401
        rows = PublishTemplate.query.filter_by(
            user_id=str(session['user_id'])
        ).order_by(PublishTemplate.created_at.desc()).all()
        return jsonify({'status': 'success', 'templates': [r.to_dict() for r in rows]})

    @app.route('/api/my/publish-templates', methods=['POST'])
    def save_template():
        if not is_logged_in():
            return jsonify({'status': 'error', 'message': '请先登录'}), 401
        data = request.json or {}
        name = (data.get('name') or '我的模板').strip()
        payload = data.get('payload') or data
        row = PublishTemplate(
            id=generate_id(),
            user_id=str(session['user_id']),
            name=name[:100],
            payload=json.dumps(payload, ensure_ascii=False),
            created_at=_now()
        )
        db.session.add(row)
        db.session.commit()
        return jsonify({'status': 'success', 'template': row.to_dict()})

    @app.route('/api/my/publish-templates/from-book/<book_id>', methods=['POST'])
    def template_from_book(book_id):
        """MyBooks「存模板」：从已有书复制 payload"""
        if not is_logged_in():
            return jsonify({'status': 'error', 'message': '请先登录'}), 401
        book = Book.query.filter_by(id=str(book_id)).first()
        if not book or str(book.owner_id) != str(session['user_id']):
            return jsonify({'status': 'error', 'message': '无权限'}), 403
        d = book.to_dict()
        payload = {k: d.get(k) for k in (
            'title', 'author', 'category', 'price', 'desc', 'contact', 'condition',
            'isbn', 'edition', 'course_code', 'campus_zone', 'dorm_building',
            'campaign_tag', 'listing_type', 'bundle_items', 'imgs'
        )}
        name = (request.json or {}).get('name') or f'模板-{book.title[:20]}'
        row = PublishTemplate(
            id=generate_id(),
            user_id=str(session['user_id']),
            name=name[:100],
            payload=json.dumps(payload, ensure_ascii=False),
            created_at=_now()
        )
        db.session.add(row)
        db.session.commit()
        return jsonify({'status': 'success', 'template': row.to_dict()})

    @app.route('/api/my/publish-templates/<tid>', methods=['DELETE'])
    def delete_template(tid):
        if not is_logged_in():
            return jsonify({'status': 'error', 'message': '请先登录'}), 401
        row = PublishTemplate.query.filter_by(
            id=str(tid), user_id=str(session['user_id'])
        ).first()
        if row:
            db.session.delete(row)
            db.session.commit()
        return jsonify({'status': 'success'})

    @app.route('/api/collections/<book_id>/price-alert', methods=['PUT'])
    def set_collection_price_alert(book_id):
        if not is_logged_in():
            return jsonify({'status': 'error', 'message': '请先登录'}), 401
        col = Collection.query.filter_by(
            book_id=str(book_id), user_id=str(session['user_id'])
        ).first()
        if not col:
            return jsonify({'status': 'error', 'message': '未收藏该书籍'}), 404
        enabled = request.json.get('enabled', True)
        col.price_alert = bool(enabled)
        db.session.commit()
        return jsonify({'status': 'success', 'price_alert': col.price_alert})

    @app.route('/api/user/subscribe-price-drop', methods=['PUT'])
    def set_subscribe_price_drop():
        if not is_logged_in():
            return jsonify({'status': 'error', 'message': '请先登录'}), 401
        user = User.query.filter_by(id=str(session['user_id'])).first()
        user.subscribe_price_drop = bool(request.json.get('enabled', True))
        db.session.commit()
        return jsonify({'status': 'success', 'subscribe_price_drop': user.subscribe_price_drop})

    @app.route('/api/public/wanted/<wanted_id>', methods=['GET'])
    def public_wanted(wanted_id):
        w = WantedPost.query.filter_by(id=str(wanted_id)).first()
        if not w or w.status != 'open':
            return jsonify({'status': 'error', 'message': '求购不存在或已关闭'}), 404
        d = w.to_dict()
        if find_wanted_matches:
            d['matches'] = find_wanted_matches(w)[:8]
        return jsonify({'status': 'success', 'wanted': d})

    @app.route('/api/public/seller/<seller_id>/books', methods=['GET'])
    def public_seller_books(seller_id):
        user = User.query.filter_by(id=str(seller_id)).first()
        if not user:
            return jsonify({'status': 'error', 'message': '用户不存在'}), 404
        books = Book.query.filter_by(owner_id=str(seller_id), status='available').all()
        stats = helpers['seller_profile_stats'](seller_id)
        stats.update(seller_view_metrics(seller_id))
        return jsonify({
            'status': 'success',
            'seller': {
                'id': user.id,
                'username': user.username,
                'school': user.school or '',
                'campus_verified': bool(user.campus_verified)
            },
            'stats': stats,
            'books': [b.to_dict() for b in books]
        })
