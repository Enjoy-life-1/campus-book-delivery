"""管理端扩展：分类/公告/校园/审计 API"""
import time

from flask import jsonify, request, session

from services.engineering import cache
from app_helpers import sms_using_webhook, SMS_WEBHOOK_HINT, find_wanted_matches, _post_gateway
from models import (
    db, User, Category, Announcement, CampusSpot, CourseTextbook,
    SemesterCampaign, WantedPost, Conversation, Message, NotificationOutbox,
    MeetingAppointment,
)
from services.campus_features import refresh_semester_campaigns, enrich_campaign_dict


def register_admin_ext_routes(app, helpers):
    """管理端扩展：分类/公告/校园 CRUD、审计与通知通道"""
    generate_id = helpers['generate_id']
    is_admin = helpers['is_admin']
    send_channel_message = helpers['send_channel_message']
    app_ref = helpers.get('app') or app

    # 分类 API
    @app.route('/api/categories', methods=['GET'])
    @cache.cached(timeout=300)
    def get_categories():
        """书籍分类（缓存 300s）；无数据时返回默认五类"""
        cats = Category.query.order_by(Category.sort_order.asc()).all()
        if not cats:
            return jsonify({'status': 'success', 'categories': [
                {'code': 'textbook', 'name': '教材教辅'},
                {'code': 'postgraduate', 'name': '考研资料'},
                {'code': 'literature', 'name': '文学小说'},
                {'code': 'professional', 'name': '专业书籍'},
                {'code': 'other', 'name': '其他书籍'},
            ]})
        return jsonify({'status': 'success', 'categories': [c.to_dict() for c in cats]})

    @app.route('/api/admin/categories', methods=['POST'])
    def admin_add_category():
        """新增书籍分类"""
        if not is_admin():
            return jsonify({'status': 'error', 'message': '无管理员权限'}), 403
        data = request.json or {}
        code = (data.get('code') or '').strip()
        name = (data.get('name') or '').strip()
        if not code or not name:
            return jsonify({'status': 'error', 'message': '分类代码和名称不能为空'}), 400
        if Category.query.filter_by(code=code).first():
            return jsonify({'status': 'error', 'message': '分类代码已存在'}), 400
        cat = Category(
            id=generate_id(),
            code=code,
            name=name,
            sort_order=int(data.get('sort_order', 99)),
            created_at=time.strftime('%Y-%m-%d %H:%M:%S')
        )
        db.session.add(cat)
        db.session.commit()
        return jsonify({'status': 'success', 'category': cat.to_dict()})

    @app.route('/api/admin/categories/<cat_id>', methods=['PUT', 'DELETE'])
    def admin_manage_category(cat_id):
        """更新或删除分类"""
        if not is_admin():
            return jsonify({'status': 'error', 'message': '无管理员权限'}), 403
        cat = Category.query.filter_by(id=str(cat_id)).first()
        if not cat:
            return jsonify({'status': 'error', 'message': '分类不存在'}), 404
        if request.method == 'DELETE':
            db.session.delete(cat)
            db.session.commit()
            return jsonify({'status': 'success', 'message': '分类已删除'})
        data = request.json or {}
        if data.get('name'):
            cat.name = data['name'].strip()
        if data.get('code'):
            cat.code = data['code'].strip()
        if 'sort_order' in data:
            cat.sort_order = int(data['sort_order'])
        db.session.commit()
        return jsonify({'status': 'success', 'category': cat.to_dict()})

    # 系统公告 API
    @app.route('/api/announcements', methods=['GET'])
    @cache.cached(timeout=120)
    def get_announcements():
        """前台可见的活跃公告（缓存 120s）"""
        anns = Announcement.query.filter_by(is_active=True).order_by(
            Announcement.created_at.desc()
        ).all()
        return jsonify({'status': 'success', 'announcements': [a.to_dict() for a in anns]})

    @app.route('/api/admin/announcements', methods=['GET', 'POST'])
    def admin_announcements():
        """公告列表 / 新建"""
        if not is_admin():
            return jsonify({'status': 'error', 'message': '无管理员权限'}), 403
        if request.method == 'GET':
            anns = Announcement.query.order_by(Announcement.created_at.desc()).all()
            return jsonify({'status': 'success', 'announcements': [a.to_dict() for a in anns]})
        data = request.json or {}
        title = (data.get('title') or '').strip()
        content = (data.get('content') or '').strip()
        if not title or not content:
            return jsonify({'status': 'error', 'message': '标题和内容不能为空'}), 400
        ann = Announcement(
            id=generate_id(),
            title=title,
            content=content,
            type=data.get('type', 'guide'),
            is_active=bool(data.get('is_active', True)),
            created_at=time.strftime('%Y-%m-%d %H:%M:%S'),
            updated_at=time.strftime('%Y-%m-%d %H:%M:%S')
        )
        db.session.add(ann)
        db.session.commit()
        return jsonify({'status': 'success', 'announcement': ann.to_dict()})

    # ========== 管理端：校园数据 CRUD ==========
    @app.route('/api/admin/campus/spots', methods=['GET', 'POST'])
    def admin_campus_spots():
        """面交点列表 / 新增"""
        if not is_admin():
            return jsonify({'status': 'error', 'message': '无管理员权限'}), 403
        if request.method == 'GET':
            rows = CampusSpot.query.order_by(CampusSpot.sort_order).all()
            return jsonify({'status': 'success', 'spots': [s.to_dict() for s in rows]})
        data = request.json or {}
        name = (data.get('name') or '').strip()
        if not name:
            return jsonify({'status': 'error', 'message': '地点名称不能为空'}), 400
        sid = (data.get('id') or '').strip() or generate_id()
        if CampusSpot.query.filter_by(id=sid).first():
            return jsonify({'status': 'error', 'message': 'ID已存在'}), 400
        spot = CampusSpot(
            id=sid, name=name,
            zone=(data.get('zone') or '西校区').strip(),
            description=(data.get('description') or '').strip(),
            sort_order=int(data.get('sort_order', 0) or 0),
            created_at=time.strftime('%Y-%m-%d %H:%M:%S')
        )
        db.session.add(spot)
        db.session.commit()
        return jsonify({'status': 'success', 'spot': spot.to_dict()})


    @app.route('/api/admin/campus/spots/<spot_id>', methods=['PUT', 'DELETE'])
    def admin_campus_spot(spot_id):
        """更新或删除面交点"""
        if not is_admin():
            return jsonify({'status': 'error', 'message': '无管理员权限'}), 403
        spot = CampusSpot.query.filter_by(id=str(spot_id)).first()
        if not spot:
            return jsonify({'status': 'error', 'message': '面交点不存在'}), 404
        if request.method == 'DELETE':
            db.session.delete(spot)
            db.session.commit()
            return jsonify({'status': 'success', 'message': '已删除'})
        data = request.json or {}
        if 'name' in data:
            spot.name = (data['name'] or '').strip()
        if 'zone' in data:
            spot.zone = (data['zone'] or '').strip()
        if 'description' in data:
            spot.description = (data['description'] or '').strip()
        if 'sort_order' in data:
            spot.sort_order = int(data['sort_order'] or 0)
        db.session.commit()
        return jsonify({'status': 'success', 'spot': spot.to_dict()})


    @app.route('/api/admin/campus/courses', methods=['GET', 'POST'])
    def admin_campus_courses():
        """课程教材列表 / 新增"""
        if not is_admin():
            return jsonify({'status': 'error', 'message': '无管理员权限'}), 403
        if request.method == 'GET':
            rows = CourseTextbook.query.order_by(CourseTextbook.college, CourseTextbook.major).all()
            return jsonify({'status': 'success', 'courses': [r.to_dict() for r in rows]})
        data = request.json or {}
        code = (data.get('course_code') or '').strip()
        if not code:
            return jsonify({'status': 'error', 'message': '课程代码不能为空'}), 400
        cid = (data.get('id') or '').strip() or f'course_{code}'
        if CourseTextbook.query.filter_by(id=cid).first():
            return jsonify({'status': 'error', 'message': '课程已存在'}), 400
        row = CourseTextbook(
            id=cid,
            college=(data.get('college') or '').strip(),
            major=(data.get('major') or '').strip(),
            course_code=code,
            course_name=(data.get('course_name') or code).strip(),
            textbook_title=(data.get('textbook_title') or '').strip(),
            textbook_author=(data.get('textbook_author') or '').strip(),
            textbook_isbn=(data.get('textbook_isbn') or '').strip(),
            created_at=time.strftime('%Y-%m-%d %H:%M:%S')
        )
        db.session.add(row)
        db.session.commit()
        return jsonify({'status': 'success', 'course': row.to_dict()})


    @app.route('/api/admin/campus/courses/<course_id>', methods=['PUT', 'DELETE'])
    def admin_campus_course(course_id):
        """更新或删除课程教材"""
        if not is_admin():
            return jsonify({'status': 'error', 'message': '无管理员权限'}), 403
        row = CourseTextbook.query.filter_by(id=str(course_id)).first()
        if not row:
            return jsonify({'status': 'error', 'message': '课程不存在'}), 404
        if request.method == 'DELETE':
            db.session.delete(row)
            db.session.commit()
            return jsonify({'status': 'success', 'message': '已删除'})
        data = request.json or {}
        for field in ('college', 'major', 'course_code', 'course_name', 'textbook_title', 'textbook_author', 'textbook_isbn'):
            if field in data:
                setattr(row, field, (data[field] or '').strip())
        db.session.commit()
        return jsonify({'status': 'success', 'course': row.to_dict()})


    @app.route('/api/admin/campus/campaigns', methods=['GET', 'POST'])
    def admin_campus_campaigns():
        """学期活动列表 / 新增（可设唯一活跃）"""
        if not is_admin():
            return jsonify({'status': 'error', 'message': '无管理员权限'}), 403
        if request.method == 'GET':
            refresh_semester_campaigns()
            rows = SemesterCampaign.query.order_by(SemesterCampaign.created_at.desc()).all()
            return jsonify({'status': 'success', 'campaigns': [enrich_campaign_dict(c) for c in rows]})
        data = request.json or {}
        title = (data.get('title') or '').strip()
        if not title:
            return jsonify({'status': 'error', 'message': '活动标题不能为空'}), 400
        cid = (data.get('id') or '').strip() or generate_id()
        if data.get('is_active'):
            SemesterCampaign.query.update({'is_active': False})
        camp = SemesterCampaign(
            id=cid, title=title,
            campaign_type=(data.get('campaign_type') or 'back_to_school').strip(),
            tag=(data.get('tag') or '').strip(),
            start_date=(data.get('start_date') or '').strip(),
            end_date=(data.get('end_date') or '').strip(),
            description=(data.get('description') or '').strip(),
            is_active=bool(data.get('is_active', False)),
            created_at=time.strftime('%Y-%m-%d %H:%M:%S')
        )
        db.session.add(camp)
        db.session.commit()
        return jsonify({'status': 'success', 'campaign': camp.to_dict()})


    @app.route('/api/admin/campus/campaigns/<camp_id>', methods=['PUT', 'DELETE'])
    def admin_campus_campaign(camp_id):
        """更新或删除学期活动"""
        if not is_admin():
            return jsonify({'status': 'error', 'message': '无管理员权限'}), 403
        camp = SemesterCampaign.query.filter_by(id=str(camp_id)).first()
        if not camp:
            return jsonify({'status': 'error', 'message': '活动不存在'}), 404
        if request.method == 'DELETE':
            db.session.delete(camp)
            db.session.commit()
            return jsonify({'status': 'success', 'message': '已删除'})
        data = request.json or {}
        if data.get('is_active'):
            SemesterCampaign.query.filter(SemesterCampaign.id != camp.id).update({'is_active': False})
        for field in ('title', 'campaign_type', 'tag', 'start_date', 'end_date', 'description'):
            if field in data:
                setattr(camp, field, (data[field] or '').strip())
        if 'is_active' in data:
            camp.is_active = bool(data['is_active'])
        db.session.commit()
        return jsonify({'status': 'success', 'campaign': camp.to_dict()})


    # ========== 管理端：求购 / 私信审计 ==========
    @app.route('/api/admin/wanted', methods=['GET'])
    def admin_wanted_list():
        """求购帖列表（含匹配在售数）"""
        if not is_admin():
            return jsonify({'status': 'error', 'message': '无管理员权限'}), 403
        rows = WantedPost.query.order_by(WantedPost.created_at.desc()).all()
        items = []
        for w in rows:
            d = w.to_dict()
            d['match_count'] = len(find_wanted_matches(w))
            items.append(d)
        return jsonify({'status': 'success', 'wanted': items})


    @app.route('/api/admin/wanted/<wanted_id>', methods=['DELETE'])
    def admin_delete_wanted(wanted_id):
        """删除求购帖"""
        if not is_admin():
            return jsonify({'status': 'error', 'message': '无管理员权限'}), 403
        w = WantedPost.query.filter_by(id=str(wanted_id)).first()
        if not w:
            return jsonify({'status': 'error', 'message': '求购不存在'}), 404
        db.session.delete(w)
        db.session.commit()
        return jsonify({'status': 'success', 'message': '已删除'})


    @app.route('/api/admin/wanted/<wanted_id>/close', methods=['PUT'])
    def admin_close_wanted(wanted_id):
        """关闭求购帖"""
        if not is_admin():
            return jsonify({'status': 'error', 'message': '无管理员权限'}), 403
        w = WantedPost.query.filter_by(id=str(wanted_id)).first()
        if not w:
            return jsonify({'status': 'error', 'message': '求购不存在'}), 404
        w.status = 'closed'
        db.session.commit()
        return jsonify({'status': 'success', 'wanted': w.to_dict()})


    @app.route('/api/admin/conversations', methods=['GET'])
    def admin_conversations():
        """私信会话审计列表"""
        if not is_admin():
            return jsonify({'status': 'error', 'message': '无管理员权限'}), 403
        convs = Conversation.query.order_by(Conversation.updated_at.desc()).limit(200).all()
        result = []
        for c in convs:
            d = c.to_dict()
            ua = User.query.filter_by(id=c.user_a_id).first()
            ub = User.query.filter_by(id=c.user_b_id).first()
            d['user_a_name'] = ua.username if ua else c.user_a_id
            d['user_b_name'] = ub.username if ub else c.user_b_id
            d['message_count'] = Message.query.filter_by(conversation_id=c.id).count()
            result.append(d)
        return jsonify({'status': 'success', 'conversations': result})


    @app.route('/api/admin/conversations/<conv_id>/messages', methods=['GET'])
    def admin_conversation_messages(conv_id):
        """查看会话消息（含面约详情）"""
        if not is_admin():
            return jsonify({'status': 'error', 'message': '无管理员权限'}), 403
        conv = Conversation.query.filter_by(id=str(conv_id)).first()
        if not conv:
            return jsonify({'status': 'error', 'message': '会话不存在'}), 404
        msgs = Message.query.filter_by(conversation_id=str(conv_id)).order_by(Message.created_at).all()
        out = []
        for m in msgs:
            d = m.to_dict()
            if not d.get('sender_name'):
                su = User.query.filter_by(id=m.sender_id).first()
                d['sender_name'] = su.username if su else m.sender_id
            if m.appointment_id:
                appt = MeetingAppointment.query.filter_by(id=m.appointment_id).first()
                if appt:
                    d['appointment'] = appt.to_dict()
            out.append(d)
        return jsonify({'status': 'success', 'conversation': conv.to_dict(), 'messages': out})


    @app.route('/api/admin/notification-outbox', methods=['GET'])
    def admin_notification_outbox():
        """短信/邮件 outbox 记录"""
        if not is_admin():
            return jsonify({'status': 'error', 'message': '无管理员权限'}), 403
        channel = (request.args.get('channel') or '').strip()
        q = NotificationOutbox.query
        if channel:
            q = q.filter_by(channel=channel)
        rows = q.order_by(NotificationOutbox.created_at.desc()).limit(300).all()
        items = []
        for r in rows:
            d = r.to_dict()
            u = User.query.filter_by(id=r.user_id).first()
            d['username'] = u.username if u else ''
            items.append(d)
        return jsonify({'status': 'success', 'records': items})


    @app.route('/api/admin/notification-outbox/<record_id>/retry', methods=['POST'])
    def admin_retry_outbox(record_id):
        """重试失败的 outbox 投递"""
        if not is_admin():
            return jsonify({'status': 'error', 'message': '无管理员权限'}), 403
        row = NotificationOutbox.query.filter_by(id=str(record_id)).first()
        if not row:
            return jsonify({'status': 'error', 'message': '记录不存在'}), 404
        status, detail = _post_gateway(row.channel, row.recipient, row.title or '', row.content or '')
        row.status = status
        if detail and status == 'failed':
            row.content = f'{(row.content or "")[:200]} [重试失败:{detail}]'
        db.session.commit()
        return jsonify({'status': 'success', 'record': row.to_dict()})


    @app.route('/api/admin/gateway/test', methods=['POST'])
    def admin_test_gateway():
        """测试短信/邮件网关连通性"""
        if not is_admin():
            return jsonify({'status': 'error', 'message': '无管理员权限'}), 403
        data = request.json or {}
        channel = (data.get('channel') or '').strip().lower()
        recipient = (data.get('recipient') or '').strip()
        if channel not in ('sms', 'email'):
            return jsonify({'status': 'error', 'message': 'channel 须为 sms 或 email'}), 400
        if not recipient:
            return jsonify({'status': 'error', 'message': '请填写收件人'}), 400
        title = '校园书递网关测试'
        content = data.get('content') or '这是一条测试消息，请忽略。'
        status, detail = send_channel_message(channel, recipient, title, content, session.get('user_id', ''))
        db.session.commit()
        if status == 'sent' and channel == 'sms' and sms_using_webhook():
            msg = f'已投递至 Webhook。{SMS_WEBHOOK_HINT}'
        elif status == 'sent':
            msg = '发送成功'
        elif status == 'simulated':
            msg = '已模拟记录'
        elif status == 'skipped':
            msg = detail or '通道已关闭'
        elif channel == 'sms' and sms_using_webhook() and 'Connection refused' in str(detail):
            msg = 'Webhook 未启动，请先运行「启动短信Webhook.bat」'
        else:
            msg = f'发送失败：{detail}'
        return jsonify({
            'status': 'success' if status in ('sent', 'simulated') else 'error',
            'gateway_status': status,
            'detail': detail,
            'message': msg,
            'webhook_mode': bool(channel == 'sms' and status == 'sent' and sms_using_webhook()),
        })


    @app.route('/api/admin/announcements/<ann_id>', methods=['PUT', 'DELETE'])
    def admin_manage_announcement(ann_id):
        """更新或删除公告"""
        if not is_admin():
            return jsonify({'status': 'error', 'message': '无管理员权限'}), 403
        ann = Announcement.query.filter_by(id=str(ann_id)).first()
        if not ann:
            return jsonify({'status': 'error', 'message': '公告不存在'}), 404
        if request.method == 'DELETE':
            db.session.delete(ann)
            db.session.commit()
            return jsonify({'status': 'success', 'message': '公告已删除'})
        data = request.json or {}
        if data.get('title'):
            ann.title = data['title'].strip()
        if data.get('content'):
            ann.content = data['content'].strip()
        if data.get('type'):
            ann.type = data['type']
        if 'is_active' in data:
            ann.is_active = bool(data['is_active'])
        ann.updated_at = time.strftime('%Y-%m-%d %H:%M:%S')
        db.session.commit()
        return jsonify({'status': 'success', 'announcement': ann.to_dict()})

