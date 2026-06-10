"""业务辅助函数（通知、书籍、会话、鉴权）"""
import json
import os
import re
import time
import urllib.parse
import urllib.request
from datetime import datetime, timedelta

from flask import jsonify, redirect, send_from_directory, session, url_for

from services.admin_compliance import effective_role, is_staff_user
from services.credit_score import compute_user_credit
from models import (
    db, User, Book, Order, Collection, WantedPost, Conversation,
    Notification, NotificationOutbox, UserFollow, PriceOffer, Review,
    CourseTextbook,
)
from services.seller_tools import seller_view_metrics

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DIST_DIR = os.path.join(BASE_DIR, 'dist')
MSG_IMAGE_EXT = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
MSG_AUDIO_EXT = {'webm', 'mp3', 'm4a', 'ogg', 'wav'}
MESSAGE_UPLOAD_DIR = os.path.join(BASE_DIR, 'static', 'uploads', 'messages')


def serve_vue_index():
    """dist/index.html 存在则返回，禁用缓存"""
    index_file = os.path.join(DIST_DIR, 'index.html')
    if os.path.exists(index_file):
        resp = send_from_directory(DIST_DIR, 'index.html')
        resp.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        resp.headers['Pragma'] = 'no-cache'
        return resp
    return None


def get_monthly_sales_value(orders=None):
    if orders is None:
        orders = [order.to_dict() for order in Order.query.all()]
    current_month_prefix = time.strftime('%Y-%m')
    return sum(
        1 for order in orders
        if order.get('created_at', '').startswith(current_month_prefix)
    )


def get_pending_reviews_value(orders=None):
    if orders is None:
        return Order.query.filter_by(status='pending').count()
    return sum(1 for order in orders if order.get('status') == 'pending')


def generate_id():
    """毫秒时间戳 ID"""
    return str(int(time.time() * 1000))


def _conv_pair(user_id, peer_id):
    """会话 user_a/b 按 id 字典序固定"""
    a, b = sorted([str(user_id), str(peer_id)])
    return a, b


def get_or_create_conversation(user_id, peer_id, book_id='', order_id='', book_title=''):
    """双用户+书籍/订单上下文唯一会话；user_a/b 按 id 排序"""
    a, b = _conv_pair(user_id, peer_id)
    book_id = str(book_id or '')
    order_id = str(order_id or '')
    conv = Conversation.query.filter_by(
        user_a_id=a, user_b_id=b, book_id=book_id, order_id=order_id
    ).first()
    if conv:
        return conv
    now = time.strftime('%Y-%m-%d %H:%M:%S')
    conv = Conversation(
        id=generate_id(),
        user_a_id=a,
        user_b_id=b,
        book_id=book_id,
        order_id=order_id,
        book_title=book_title or '',
        last_preview='',
        created_at=now,
        updated_at=now,
    )
    db.session.add(conv)
    db.session.commit()
    return conv


def _user_brief(uid):
    """私信/列表用用户摘要"""
    u = User.query.filter_by(id=str(uid)).first()
    return {'id': str(uid), 'username': u.username if u else '用户', 'avatar': (u.avatar or '') if u else ''}


def _system_notify_enabled(channel):
    from models import Setting
    settings = Setting.get_all_as_dict()
    if channel == 'email':
        val = settings.get('notify_email_enabled', settings.get('enableEmailNotification', True))
    else:
        val = settings.get('notify_sms_enabled', True)
    return val is not False and str(val).lower() != 'false'


def _valid_webhook_url(url):
    return url.startswith('http://') or url.startswith('https://')


def sms_channel_configured():
    """阿里云 SMS 或 Webhook 任一可用"""
    from services.sms_aliyun import aliyun_sms_configured
    return aliyun_sms_configured() or _valid_webhook_url(_gateway_url('sms'))


def sms_using_webhook():
    """开发环境优先 Webhook，不发真实短信"""
    prefer = os.environ.get('SMS_PREFER_WEBHOOK', '1').lower() not in ('0', 'false', 'no')
    return prefer and _valid_webhook_url(_gateway_url('sms'))


SMS_WEBHOOK_HINT = '请查看「启动短信Webhook」窗口或 logs/sms_webhook.log（Webhook 模式不会发到手机）'


def _gateway_url(channel):
    from models import Setting
    settings = Setting.get_all_as_dict()
    if channel == 'email':
        return (os.environ.get('EMAIL_WEBHOOK_URL') or settings.get('email_webhook_url') or '').strip()
    return (os.environ.get('SMS_WEBHOOK_URL') or settings.get('sms_webhook_url') or '').strip()


def _post_sms(recipient, title, content, template_params=None):
    """Webhook 优先 → 阿里云 → simulated"""
    from services.sms_aliyun import aliyun_sms_configured, send_verify_code, send_notify_sms
    import re

    hook = _gateway_url('sms')
    prefer_webhook = os.environ.get('SMS_PREFER_WEBHOOK', '1').lower() not in ('0', 'false', 'no')

    def _try_webhook():
        if not _valid_webhook_url(hook):
            return None
        payload = json.dumps({'phone': recipient, 'title': title, 'content': content}).encode('utf-8')
        try:
            req = urllib.request.Request(
                hook, data=payload,
                headers={'Content-Type': 'application/json'}, method='POST',
            )
            urllib.request.urlopen(req, timeout=8)
            return 'sent', ''
        except Exception as e:
            return 'failed', str(e)

    if prefer_webhook and _valid_webhook_url(hook):
        r = _try_webhook()
        if r:
            return r

    if aliyun_sms_configured():
        params = dict(template_params or {})
        if not params.get('code') and title == '验证码':
            m = re.search(r'(\d{6})', content or '')
            if m:
                params['code'] = m.group(1)
        if params.get('code'):
            return send_verify_code(recipient, params['code'])
        st, detail = send_notify_sms(recipient, content)
        if st == 'sent':
            return st, detail
        if title == '验证码':
            return st, detail

    if not prefer_webhook and _valid_webhook_url(hook):
        r = _try_webhook()
        if r:
            return r

    return 'simulated', '未配置短信通道'


def _post_gateway(channel, recipient, title, content, template_params=None):
    if channel == 'sms':
        return _post_sms(recipient, title, content, template_params)
    hook = _gateway_url(channel)
    if not hook:
        return 'simulated', '未配置 Webhook，仅记录 outbox'
    if not _valid_webhook_url(hook):
        return 'failed', f'无效的 Webhook 地址：{hook}'
    payload_key = 'email' if channel == 'email' else 'phone'
    try:
        payload = json.dumps({
            payload_key: recipient, 'title': title, 'content': content
        }).encode('utf-8')
        req = urllib.request.Request(
            hook, data=payload,
            headers={'Content-Type': 'application/json'}, method='POST',
        )
        urllib.request.urlopen(req, timeout=8)
        return 'sent', ''
    except Exception as e:
        return 'failed', str(e)


def _log_outbox(user_id, channel, recipient, title, content, status):
    db.session.add(NotificationOutbox(
        id=generate_id(),
        user_id=str(user_id or ''),
        channel=channel,
        recipient=recipient,
        title=title,
        content=(content or '')[:500],
        status=status,
        created_at=time.strftime('%Y-%m-%d %H:%M:%S'),
    ))


def send_channel_message(channel, recipient, title, content, user_id='', template_params=None):
    """统一外发入口：校验开关 → 发送 → 写 outbox"""
    recipient = (recipient or '').strip()
    if not recipient:
        return 'failed', '收件人为空'
    if channel == 'sms' and not _system_notify_enabled('sms'):
        return 'skipped', '短信通道已关闭'
    if channel == 'email' and not _system_notify_enabled('email'):
        return 'skipped', '邮件通道已关闭'
    status, detail = _post_gateway(channel, recipient, title, content, template_params)
    body = content
    if detail and status == 'failed':
        body = f'{content[:200]} [{detail}]'
    _log_outbox(user_id, channel, recipient, title, body, status)
    return status, detail


def deliver_external_notification(user_id, title, content=''):
    """用户开启 notify_email/sms 时外发"""
    user = User.query.filter_by(id=str(user_id)).first()
    if not user:
        return
    body = content or title
    if _system_notify_enabled('email') and user.notify_email and (user.email or '').strip():
        send_channel_message('email', user.email.strip(), title, body, user_id)
    if _system_notify_enabled('sms') and user.notify_sms and (user.phone or '').strip():
        send_channel_message('sms', user.phone.strip(), title, body[:70], user_id)


def push_notification(user_id, ntype, title, content='', link=''):
    """站内通知 + 可选邮件/短信外发"""
    if not user_id:
        return
    n = Notification(
        id=generate_id(),
        user_id=str(user_id),
        ntype=ntype,
        title=title,
        content=content,
        link=link or '',
        is_read=False,
        created_at=time.strftime('%Y-%m-%d %H:%M:%S'),
    )
    db.session.add(n)
    deliver_external_notification(user_id, title, content)


def notify_price_drop(book, old_price):
    """收藏且开启 price_alert 的用户收到降价通知"""
    if old_price is None or book.price is None:
        return
    if float(book.price) >= float(old_price):
        return
    for col in Collection.query.filter_by(book_id=str(book.id)).all():
        if col.price_alert is False:
            continue
        u = User.query.filter_by(id=str(col.user_id)).first()
        if u and u.subscribe_price_drop is False:
            continue
        snap = col.collected_price
        if snap is not None and float(book.price) < float(snap):
            push_notification(
                col.user_id, 'price_drop',
                f'收藏书籍降价了：{book.title}',
                f'现价 ¥{book.price}，收藏时 ¥{snap}',
                f'/book/{book.id}',
            )


def notify_seller_followers_new_book(book):
    """卖家上架 → 粉丝站内通知"""
    seller_id = str(book.owner_id or '')
    if not seller_id:
        return
    for f in UserFollow.query.filter_by(seller_id=seller_id).all():
        if str(f.follower_id) == seller_id:
            continue
        push_notification(
            f.follower_id, 'new_book',
            f'关注的卖家上新：{book.title}',
            f'售价 ¥{book.price}',
            f'/book/{book.id}',
        )


def seller_profile_stats(user_id):
    """卖家主页：销量、评分、浏览转化、信用分"""
    uid = str(user_id)
    books = Book.query.filter_by(owner_id=uid, status='available').all()
    completed = Order.query.filter_by(seller_id=uid, status='completed').count()
    total_sales = Order.query.filter(
        Order.seller_id == uid,
        Order.status.in_(['completed', 'pickup', 'pending']),
    ).count()
    reviews = Review.query.filter_by(reviewed_user_id=uid).all()
    if reviews:
        avg = sum(
            (r.description_rating or r.service_rating or 0) + (r.service_rating or 0) +
            (r.condition_rating or 0) + (r.efficiency_rating or 0)
            for r in reviews
        ) / (len(reviews) * 4)
        good_rate = sum(1 for r in reviews if (r.service_rating or 0) >= 4) / len(reviews) * 100
    else:
        avg = 5.0
        good_rate = 100.0
    if completed >= 20:
        credit = '金牌卖家'
    elif completed >= 5:
        credit = '信誉良好'
    else:
        credit = '新手卖家'
    month_ago = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d %H:%M:%S')
    month_sales = Order.query.filter(
        Order.seller_id == uid, Order.status == 'completed',
        Order.created_at >= month_ago,
    ).count()
    pending_offers = PriceOffer.query.filter_by(seller_id=uid, status='pending').count()
    exchange_orders = Order.query.filter(
        Order.seller_id == uid, Order.order_type == 'exchange',
    ).count()
    views = seller_view_metrics(uid)
    seller = User.query.filter_by(id=uid).first()
    credit_info = compute_user_credit(seller) if seller else {}
    return {
        'on_sale_count': len(books),
        'completed_count': completed,
        'total_orders': total_sales,
        'month_sales': month_sales,
        'pending_offers': pending_offers,
        'exchange_orders': exchange_orders,
        'review_count': len(reviews),
        'avg_rating': round(avg, 1),
        'good_rate': round(good_rate, 1),
        'credit_tag': credit_info.get('credit_tag') or credit,
        'credit_score': credit_info.get('score', 100),
        'credit_level': credit_info.get('level', '良好'),
        'total_views': views['total_views'],
        'conversion_rate': views['conversion_rate'],
    }


def find_similar_books(book, limit=6):
    """ISBN/分类/同卖家/标题相似度打分"""
    if not book:
        return []
    uid = str(book.owner_id or '')
    isbn = (book.isbn or '').strip()
    cat = book.category or ''
    title = book.title or ''
    candidates = Book.query.filter(Book.status == 'available', Book.id != book.id).all()
    scored = []
    for b in candidates:
        score = 0
        if isbn and b.isbn and isbn == (b.isbn or '').strip():
            score += 10
        if cat and b.category == cat:
            score += 4
        if str(b.owner_id) == uid:
            score += 3
        if title and b.title and title[:4] in b.title:
            score += 2
        if score > 0:
            scored.append((score, b))
    scored.sort(key=lambda x: -x[0])
    return [b.to_dict() for _, b in scored[:limit]]


def find_wanted_matches(wanted):
    """求购与在售书 ISBN/书名/预算 打分匹配"""
    wanted_uid = str(wanted.user_id)
    title_kw = (wanted.title or '').strip().lower()
    isbn = (wanted.isbn or '').strip()
    max_price = wanted.max_price
    books = Book.query.filter_by(status='available').all()
    matches = []
    for book in books:
        if str(book.owner_id or '') == wanted_uid:
            continue
        score = 0
        book_isbn = (book.isbn or '').strip()
        book_title = (book.title or '').lower()
        if isbn and book_isbn and (isbn in book_isbn or book_isbn in isbn):
            score += 10
        if title_kw and title_kw in book_title:
            score += 6
        elif title_kw:
            for word in re.split(r'\s+', title_kw):
                if len(word) >= 2 and word in book_title:
                    score += 2
        if max_price is not None and book.price is not None and float(book.price) <= float(max_price):
            score += 1
        if score > 0:
            item = book.to_dict()
            item['match_score'] = score
            matches.append(item)
    matches.sort(key=lambda x: (-x.get('match_score', 0), x.get('price', 0)))
    return matches


def enrich_book_dict(book_dict, owner=None):
    """补充降价倒计时、卖家认证/校区等展示字段"""
    until = (book_dict.get('price_drop_until') or '').strip()
    book_dict['is_price_dropping'] = False
    book_dict['price_drop_seconds_left'] = 0
    if until:
        try:
            end = datetime.strptime(until[:19], '%Y-%m-%d %H:%M:%S')
            if end > datetime.now():
                book_dict['is_price_dropping'] = True
                book_dict['price_drop_seconds_left'] = int((end - datetime.now()).total_seconds())
        except ValueError:
            pass
    if owner:
        book_dict['seller_school'] = owner.school or ''
        book_dict['seller_dorm'] = owner.dorm_building or ''
        book_dict['seller_zone'] = owner.campus_zone or ''
        book_dict['seller_verified'] = bool(owner.campus_verified)
    return book_dict


def notify_wanted_match_for_book(book):
    """新书上架时通知匹配的 open 求购"""
    if (book.status or '') != 'available':
        return
    for w in WantedPost.query.filter_by(status='open').all():
        matches = find_wanted_matches(w)
        if any(str(m.get('id')) == str(book.id) for m in matches):
            push_notification(
                w.user_id, 'new_book', '求购匹配提醒',
                f'您求购的《{w.title}》有匹配书籍《{book.title}》上架',
                f'/wanted/{w.id}',
            )


def filter_books_campus(all_books, args):
    """列表 API 后置过滤：同校/楼栋/课程/专场/认证卖家"""
    same_school = (args.get('same_school') or '').lower() == 'true'
    dorm = (args.get('dorm_building') or '').strip()
    course_code = (args.get('course_code') or '').strip()
    campaign = (args.get('campaign') or args.get('campaign_tag') or '').strip()
    zone = (args.get('campus_zone') or '').strip()

    owner_ids = list({str(b.get('owner_id') or '') for b in all_books if b.get('owner_id')})
    owners = {}
    if owner_ids:
        for u in User.query.filter(User.id.in_(owner_ids)).all():
            owners[str(u.id)] = u

    if same_school and is_logged_in():
        me = User.query.filter_by(id=str(session['user_id'])).first()
        if me and me.school_id:
            sid = str(me.school_id)
            all_books = [b for b in all_books
                         if str(b.get('school_id') or '') == sid or
                         (owners.get(str(b.get('owner_id'))) and
                          str(owners[str(b['owner_id'])].school_id or '') == sid)]
        elif me and (me.school or '').strip():
            my_school = (me.school or '').strip()
            all_books = [b for b in all_books
                         if owners.get(str(b.get('owner_id'))) and
                         (owners[str(b['owner_id'])].school or '').strip() == my_school]

    if dorm:
        all_books = [b for b in all_books
                     if (b.get('dorm_building') or '') == dorm or
                     (owners.get(str(b.get('owner_id'))) and
                      (owners[str(b['owner_id'])].dorm_building or '') == dorm)]

    if zone:
        all_books = [b for b in all_books
                     if (b.get('campus_zone') or '') == zone or
                     (owners.get(str(b.get('owner_id'))) and
                      (owners[str(b['owner_id'])].campus_zone or '') == zone)]

    if course_code:
        ct = CourseTextbook.query.filter_by(course_code=course_code).first()
        kw = (ct.textbook_title if ct else '').lower()
        all_books = [b for b in all_books
                     if (b.get('course_code') or '') == course_code or
                     (kw and kw in (b.get('title') or '').lower()) or
                     (ct and ct.textbook_isbn and ct.textbook_isbn in (b.get('isbn') or ''))]

    if campaign:
        all_books = [b for b in all_books if (b.get('campaign_tag') or '') == campaign]

    verified_only = (args.get('verified_only') or '').lower() == 'true'
    if verified_only:
        all_books = [b for b in all_books
                     if owners.get(str(b.get('owner_id'))) and
                     owners[str(b['owner_id'])].campus_verified]

    for b in all_books:
        enrich_book_dict(b, owners.get(str(b.get('owner_id'))))
    return all_books


def is_logged_in():
    return 'user_id' in session


def is_admin():
    """管理端登录 portal=admin 且 staff 角色"""
    if not is_logged_in():
        return False
    if session.get('login_portal') != 'admin':
        return False
    user = User.query.filter_by(id=str(session['user_id'])).first()
    return is_staff_user(user) if user else False


def is_full_admin():
    """role=admin 的超级管理员"""
    if not is_admin():
        return False
    user = User.query.filter_by(id=str(session['user_id'])).first()
    return effective_role(user) == 'admin' if user else False


def serve_vue_or_503():
    """无 dist 时 503 JSON 提示 npm run build"""
    vue_resp = serve_vue_index()
    if vue_resp:
        return vue_resp
    return jsonify({'status': 'error', 'message': '前端未构建，请执行 npm run build'}), 503


def admin_vue_page():
    """/admin/* SPA：校验 admin 登录后返回 index.html"""
    if 'user_id' not in session or session.get('login_portal') != 'admin':
        return redirect('/admin/login')
    if not is_admin():
        return redirect(url_for('index'))
    return serve_vue_or_503()


def build_route_helpers(flask_app):
    """注入各 route 模块共用的 helpers 字典"""
    from services.campus_features import appointment_conflict
    from routes.route_orders import orders_csv_response
    return {
        'app': flask_app,
        'generate_id': generate_id,
        'is_logged_in': is_logged_in,
        'is_admin': is_admin,
        'is_full_admin': is_full_admin,
        'push_notification': push_notification,
        'send_channel_message': send_channel_message,
        'get_or_create_conversation': get_or_create_conversation,
        '_user_brief': _user_brief,
        'seller_profile_stats': seller_profile_stats,
        'filter_books_campus': filter_books_campus,
        'enrich_book_dict': enrich_book_dict,
        'notify_price_drop': notify_price_drop,
        'notify_seller_followers_new_book': notify_seller_followers_new_book,
        'notify_wanted_match_for_book': notify_wanted_match_for_book,
        'find_similar_books': find_similar_books,
        'find_wanted_matches': find_wanted_matches,
        'get_monthly_sales_value': get_monthly_sales_value,
        'get_pending_reviews_value': get_pending_reviews_value,
        'orders_csv_response': orders_csv_response,
        'MESSAGE_UPLOAD_DIR': MESSAGE_UPLOAD_DIR,
        'MSG_IMAGE_EXT': MSG_IMAGE_EXT,
        'MSG_AUDIO_EXT': MSG_AUDIO_EXT,
        'appointment_conflict': appointment_conflict,
    }
