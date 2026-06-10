"""校园场景深化：课表导入、批量挂书、宿舍地图、面交冲突、学期活动、环保统计"""
import json
import re
import time
from datetime import datetime, timedelta

from flask import jsonify, request, session

from models import (
    db, User, Book, Order, CourseTextbook, SemesterCampaign,
    CampusSpot, MeetingAppointment, Conversation, Setting
)
from .campus_seed import DORM_MAP

PLACEHOLDER_IMG = 'https://picsum.photos/seed/campusbook/400/500'
CONFLICT_MINUTES = 60


def parse_meeting_time(raw):
    """解析面约时间字符串为 datetime"""
    s = (raw or '').strip()[:19]
    for fmt in ('%Y-%m-%d %H:%M', '%Y-%m-%d %H:%M:%S', '%Y/%m/%d %H:%M'):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    return None


def appointment_conflict(uid, meeting_time_str, exclude_id=None):
    """同一用户 ±60 分钟内已有 pending/confirmed 预约则冲突"""
    dt = parse_meeting_time(meeting_time_str)
    if not dt:
        return None
    window = timedelta(minutes=CONFLICT_MINUTES)
    start, end = dt - window, dt + window
    conv_ids = set()
    for c in Conversation.query.filter(
        db.or_(Conversation.user_a_id == uid, Conversation.user_b_id == uid)
    ).all():
        conv_ids.add(c.id)
    if not conv_ids:
        return None
    q = MeetingAppointment.query.filter(
        MeetingAppointment.conversation_id.in_(list(conv_ids)),
        MeetingAppointment.status.in_(('pending', 'confirmed'))
    )
    if exclude_id:
        q = q.filter(MeetingAppointment.id != str(exclude_id))
    for appt in q.all():
        other = parse_meeting_time(appt.meeting_time)
        if other and start <= other <= end:
            return appt
    return None


def refresh_semester_campaigns():
    """按起止日期自动启用当前学期活动"""
    today = datetime.now().strftime('%m-%d')

    def in_range(start, end):
        if not start or not end:
            return False
        if start <= end:
            return start <= today <= end
        return today >= start or today <= end

    chosen = None
    for c in SemesterCampaign.query.all():
        if in_range((c.start_date or '').strip(), (c.end_date or '').strip()):
            chosen = c
            break
    if not chosen:
        return
    SemesterCampaign.query.update({'is_active': False})
    chosen.is_active = True
    db.session.commit()


def campaign_progress(camp):
    """返回 0-100 活动进度（用于可视化）"""
    start = (camp.start_date or '').strip()
    end = (camp.end_date or '').strip()
    if not start or not end:
        return 0
    year = datetime.now().year
    try:
        s = datetime.strptime(f'{year}-{start}', '%Y-%m-%d')
        e = datetime.strptime(f'{year}-{end}', '%Y-%m-%d')
        if e < s:
            e = e.replace(year=year + 1)
        now = datetime.now()
        if now <= s:
            return 0
        if now >= e:
            return 100
        return int((now - s).total_seconds() / max((e - s).total_seconds(), 1) * 100)
    except ValueError:
        return 0


def parse_schedule_text(text):
    """课表文本：每行 课程代码,课程名"""
    rows = []
    for line in (text or '').splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        parts = re.split(r'[,，\t]+', line)
        code = parts[0].strip().upper()
        name = parts[1].strip() if len(parts) > 1 else ''
        if code:
            rows.append({'course_code': code, 'course_name': name})
    return rows


def enrich_campaign_dict(c):
    """学期活动 dict + progress_pct / phase"""
    d = c.to_dict()
    d['progress_pct'] = campaign_progress(c)
    d['phase'] = '进行中' if d['progress_pct'] in range(1, 100) else (
        '未开始' if d['progress_pct'] == 0 else '已结束'
    )
    return d


def textbook_eco_stats():
    """环保统计：成交册数、ISBN 复用、估算省纸/减碳"""
    completed = Order.query.filter_by(status='completed').count()
    sold_books = Book.query.filter_by(status='sold').count()
    isbn_cnt = db.session.query(Book.isbn).filter(
        Book.isbn != '', Book.isbn.isnot(None),
        Book.status.in_(('sold', 'available'))
    ).distinct().count()
    reuse_orders = Order.query.filter_by(status='completed', order_type='sale').count()
    paper_kg = round((completed + sold_books) * 0.45, 1)
    return {
        'completed_orders': completed,
        'sold_listings': sold_books,
        'distinct_isbn': isbn_cnt,
        'reuse_transactions': reuse_orders,
        'estimated_paper_saved_kg': paper_kg,
        'co2_saved_kg': round(paper_kg * 1.2, 1)
    }


def register_campus_features(app, helpers):
    """注册宿舍地图、课表导入、批量挂书、环保统计、学期活动 API"""
    is_logged_in = helpers['is_logged_in']
    generate_id = helpers['generate_id']
    is_admin = helpers.get('is_admin')

    @app.route('/api/campus/dorm-map', methods=['GET'])
    def dorm_map():
        spots = CampusSpot.query.order_by(CampusSpot.sort_order).all()
        dorm_map_data = DORM_MAP
        row = Setting.query.filter_by(key='dorm_map').first()
        if row and row.value:
            try:
                parsed = json.loads(row.value) if isinstance(row.value, str) else row.value
                if isinstance(parsed, list) and parsed:
                    dorm_map_data = parsed
            except (json.JSONDecodeError, TypeError):
                pass
        return jsonify({
            'status': 'success',
            'dorms': dorm_map_data,
            'spots': [s.to_dict() for s in spots]
        })

    @app.route('/api/my/schedule', methods=['GET'])
    def my_schedule_get():
        if not is_logged_in():
            return jsonify({'status': 'error', 'message': '请先登录'}), 401
        u = User.query.filter_by(id=str(session['user_id'])).first()
        items = []
        if u and u.schedule_json:
            try:
                items = json.loads(u.schedule_json)
            except (json.JSONDecodeError, TypeError):
                items = []
        return jsonify({'status': 'success', 'schedule': items})

    @app.route('/api/my/schedule/import', methods=['POST'])
    def my_schedule_import():
        """粘贴课表文本 → 关联 CourseTextbook → 存 schedule_json"""
        if not is_logged_in():
            return jsonify({'status': 'error', 'message': '请先登录'}), 401
        data = request.json or {}
        if data.get('courses'):
            rows = data['courses']
        else:
            rows = parse_schedule_text(data.get('text') or '')
        if not rows:
            return jsonify({'status': 'error', 'message': '请粘贴课表，每行：课程代码,课程名'}), 400
        merged = {}
        for r in rows:
            code = (r.get('course_code') or '').strip().upper()
            if not code:
                continue
            ct = CourseTextbook.query.filter_by(course_code=code).first()
            merged[code] = {
                'course_code': code,
                'course_name': (r.get('course_name') or (ct.course_name if ct else code)).strip(),
                'textbook_title': ct.textbook_title if ct else '',
                'textbook_isbn': ct.textbook_isbn if ct else ''
            }
        items = list(merged.values())
        u = User.query.filter_by(id=str(session['user_id'])).first()
        u.schedule_json = json.dumps(items, ensure_ascii=False)
        db.session.commit()
        return jsonify({'status': 'success', 'schedule': items, 'count': len(items)})

    @app.route('/api/my/schedule/batch-publish', methods=['POST'])
    def my_schedule_batch_publish():
        """按课表批量创建在售书籍（跳过已有同课程）"""
        if not is_logged_in():
            return jsonify({'status': 'error', 'message': '请先登录'}), 401
        u = User.query.filter_by(id=str(session['user_id'])).first()
        if not u or not u.schedule_json:
            return jsonify({'status': 'error', 'message': '请先导入课表'}), 400
        try:
            schedule = json.loads(u.schedule_json)
        except (json.JSONDecodeError, TypeError):
            return jsonify({'status': 'error', 'message': '课表数据无效'}), 400
        data = request.json or {}
        default_price = float(data.get('price') or 15)
        condition = (data.get('condition') or '九成新').strip()
        contact = (data.get('contact') or u.phone or u.email or '').strip()
        if not contact:
            return jsonify({'status': 'error', 'message': '请填写联系方式'}), 400
        created = []
        now = time.strftime('%Y-%m-%d %H:%M:%S')
        for item in schedule:
            code = (item.get('course_code') or '').strip()
            ct = CourseTextbook.query.filter_by(course_code=code).first()
            title = (item.get('textbook_title') or (ct.textbook_title if ct else '') or item.get('course_name') or code).strip()
            if not title:
                continue
            exists = Book.query.filter_by(
                owner_id=str(u.id), course_code=code, status='available'
            ).first()
            if exists:
                continue
            isbn = (item.get('textbook_isbn') or (ct.textbook_isbn if ct else '') or '').strip()
            author = (ct.textbook_author if ct else '未知作者') or '未知作者'
            bid = generate_id()
            book = Book(
                id=bid,
                title=title,
                author=author,
                category='textbook',
                price=default_price,
                desc=f'课程 {code} 教材转让',
                description=f'课程 {code} 教材转让',
                imgs=json.dumps([PLACEHOLDER_IMG], ensure_ascii=False),
                image=PLACEHOLDER_IMG,
                cover_url=PLACEHOLDER_IMG,
                contact=contact,
                stock=1,
                status='available',
                condition=condition,
                isbn=isbn,
                course_code=code,
                campus_zone=u.campus_zone or '西校区',
                dorm_building=u.dorm_building or '',
                school_id=u.school_id or '',
                owner_id=str(u.id),
                owner_name=u.username,
                seller=u.username,
                sellerId=str(u.id),
                createTime=time.strftime('%Y-%m-%d'),
                created_at=now,
                publish_date=time.strftime('%Y-%m-%d')
            )
            db.session.add(book)
            created.append(book.to_dict())
        db.session.commit()
        return jsonify({'status': 'success', 'created': created, 'count': len(created)})

    @app.route('/api/admin/stats/eco', methods=['GET'])
    def admin_eco_stats():
        if not is_admin():
            return jsonify({'status': 'error', 'message': '无管理员权限'}), 403
        return jsonify({'status': 'success', 'stats': textbook_eco_stats()})

    @app.route('/api/semester/campaigns', methods=['GET'])
    def semester_campaigns_list():
        refresh_semester_campaigns()
        rows = SemesterCampaign.query.order_by(SemesterCampaign.created_at.desc()).all()
        return jsonify({
            'status': 'success',
            'campaigns': [enrich_campaign_dict(c) for c in rows]
        })
