"""私信/议价/通知/卖家 API"""
import json
import os
import time

from flask import jsonify, request, session

from services.admin_compliance import match_sensitive, user_mute_blocked
from services.campus_features import appointment_conflict
from services.messaging import push_chat_event
from models import (
    db, User, Book, Order, Conversation, Message, MeetingAppointment,
    PriceOffer, Notification, UserBlock, UserFollow,
)


def register_messaging_routes(app, helpers):
    """注册私信、面交预约、议价、通知、关注/拉黑 API"""
    generate_id = helpers['generate_id']
    is_logged_in = helpers['is_logged_in']
    is_admin = helpers['is_admin']
    push_notification = helpers['push_notification']
    get_or_create_conversation = helpers['get_or_create_conversation']
    _user_brief = helpers['_user_brief']
    seller_profile_stats = helpers['seller_profile_stats']
    MESSAGE_UPLOAD_DIR = helpers['MESSAGE_UPLOAD_DIR']
    MSG_IMAGE_EXT = helpers['MSG_IMAGE_EXT']
    MSG_AUDIO_EXT = helpers['MSG_AUDIO_EXT']
    app_ref = helpers.get('app') or app

    # ========== 站内私信 + 面交预约 ==========
    @app.route('/api/conversations', methods=['GET'])
    def list_conversations():
        """会话列表；过滤拉黑；统计 unread_total"""
        if not is_logged_in():
            return jsonify({'status': 'error', 'message': '请先登录'}), 401
        uid = str(session['user_id'])
        blocked = {r.blocked_id for r in UserBlock.query.filter_by(blocker_id=uid).all()}
        convs = Conversation.query.filter(
            db.or_(Conversation.user_a_id == uid, Conversation.user_b_id == uid)
        ).order_by(Conversation.updated_at.desc()).all()
        result = []
        for c in convs:
            peer_id = c.peer_id_for(uid)
            if peer_id in blocked:
                continue
            peer = _user_brief(peer_id)
            unread = Message.query.filter_by(
                conversation_id=c.id, is_read=False
            ).filter(Message.sender_id != uid).count()
            item = c.to_dict(uid)
            item['peer'] = peer
            item['unread'] = unread
            result.append(item)
        total_unread = sum(x['unread'] for x in result)
        return jsonify({'status': 'success', 'conversations': result, 'unread_total': total_unread})


    @app.route('/api/conversations', methods=['POST'])
    def start_conversation():
        """创建或复用会话；可关联 book_id / order_id"""
        if not is_logged_in():
            return jsonify({'status': 'error', 'message': '请先登录'}), 401
        data = request.json or {}
        peer_id = str(data.get('peer_id', ''))
        if not peer_id:
            return jsonify({'status': 'error', 'message': '缺少对方用户ID'}), 400
        if peer_id == str(session['user_id']):
            return jsonify({'status': 'error', 'message': '不能与自己聊天'}), 400
        if not User.query.filter_by(id=peer_id).first():
            return jsonify({'status': 'error', 'message': '用户不存在'}), 404
        if UserBlock.query.filter_by(blocker_id=str(session['user_id']), blocked_id=peer_id).first():
            return jsonify({'status': 'error', 'message': '已拉黑该用户，无法发起会话'}), 403
        if UserBlock.query.filter_by(blocker_id=peer_id, blocked_id=str(session['user_id'])).first():
            return jsonify({'status': 'error', 'message': '对方已将您拉黑'}), 403
        book_id = str(data.get('book_id', '') or '')
        order_id = str(data.get('order_id', '') or '')
        book_title = ''
        if book_id:
            book = Book.query.filter_by(id=book_id).first()
            if book:
                book_title = book.title
        elif order_id:
            order = Order.query.filter_by(id=order_id).first()
            if order:
                book_title = order.book_title or ''
        conv = get_or_create_conversation(
            session['user_id'], peer_id, book_id, order_id, book_title
        )
        peer = _user_brief(peer_id)
        d = conv.to_dict(session['user_id'])
        d['peer'] = peer
        return jsonify({'status': 'success', 'conversation': d})


    @app.route('/api/conversations/<conv_id>/messages', methods=['GET'])
    def get_messages(conv_id):
        """拉取消息；since 增量；打开时标记已读"""
        if not is_logged_in():
            return jsonify({'status': 'error', 'message': '请先登录'}), 401
        uid = str(session['user_id'])
        conv = Conversation.query.filter_by(id=str(conv_id)).first()
        if not conv or uid not in (conv.user_a_id, conv.user_b_id):
            return jsonify({'status': 'error', 'message': '会话不存在或无权访问'}), 403
        since = (request.args.get('since') or '').strip()
        q = Message.query.filter_by(conversation_id=str(conv_id))
        if since:
            q = q.filter(Message.created_at > since)
        rows = q.order_by(Message.created_at.asc()).all()
        msgs = []
        for m in rows:
            appt = None
            if m.msg_type == 'appointment' and m.appointment_id:
                appt = MeetingAppointment.query.filter_by(id=m.appointment_id).first()
            msgs.append(m.to_dict(appt))
        now = time.strftime('%Y-%m-%d %H:%M:%S')
        to_mark = Message.query.filter_by(
            conversation_id=str(conv_id), is_read=False
        ).filter(Message.sender_id != uid).all()
        if to_mark:
            for m in to_mark:
                m.is_read = True
                m.read_at = now
            db.session.commit()
            push_chat_event(str(conv_id), {
                'type': 'read',
                'conv_id': str(conv_id),
                'reader_id': uid,
                'read_at': now
            }, exclude_user=uid)
        peer = _user_brief(conv.peer_id_for(uid))
        return jsonify({
            'status': 'success',
            'messages': msgs,
            'conversation': conv.to_dict(uid),
            'peer': peer
        })


    def _message_preview(msg_type, content, media_url=''):
        """会话列表最后一条预览文案"""
        if msg_type == 'image':
            return '[图片]'
        if msg_type == 'audio':
            return '[语音]'
        if msg_type == 'location':
            return '[位置]' + (content[:40] if content else '')
        return (content or media_url or '')[:200]


    @app.route('/api/messages/upload', methods=['POST'])
    def upload_message_media():
        """私信图片/语音上传"""
        if not is_logged_in():
            return jsonify({'status': 'error', 'message': '请先登录'}), 401
        f = request.files.get('file')
        if not f or not f.filename:
            return jsonify({'status': 'error', 'message': '请选择文件'}), 400
        ext = f.filename.rsplit('.', 1)[-1].lower() if '.' in f.filename else ''
        kind = (request.form.get('kind') or '').strip().lower()
        if kind == 'audio':
            if ext not in MSG_AUDIO_EXT:
                return jsonify({'status': 'error', 'message': '不支持的音频格式'}), 400
            msg_type = 'audio'
        else:
            if ext not in MSG_IMAGE_EXT:
                return jsonify({'status': 'error', 'message': '不支持的图片格式'}), 400
            msg_type = 'image'
        data = f.read()
        if len(data) > 5 * 1024 * 1024:
            return jsonify({'status': 'error', 'message': '文件不能超过 5MB'}), 400
        os.makedirs(MESSAGE_UPLOAD_DIR, exist_ok=True)
        fname = f'{generate_id()}.{ext}'
        path = os.path.join(MESSAGE_UPLOAD_DIR, fname)
        with open(path, 'wb') as out:
            out.write(data)
        url = f'/static/uploads/messages/{fname}'
        return jsonify({'status': 'success', 'url': url, 'msg_type': msg_type})


    @app.route('/api/conversations/<conv_id>/messages', methods=['POST'])
    def send_message(conv_id):
        """发送文本/图片/语音/位置；敏感词+禁言校验；WebSocket push_chat_event"""
        if not is_logged_in():
            return jsonify({'status': 'error', 'message': '请先登录'}), 401
        uid = str(session['user_id'])
        conv = Conversation.query.filter_by(id=str(conv_id)).first()
        if not conv or uid not in (conv.user_a_id, conv.user_b_id):
            return jsonify({'status': 'error', 'message': '会话不存在或无权访问'}), 403
        sender = User.query.filter_by(id=uid).first()
        mute_msg = user_mute_blocked(sender)
        if mute_msg:
            return jsonify({'status': 'error', 'message': mute_msg}), 403
        data = request.json or {}
        msg_type = (data.get('msg_type') or 'text').strip().lower()
        content = (data.get('content') or '').strip()
        media_url = (data.get('media_url') or '').strip()
        media_meta = data.get('media_meta')
        if msg_type not in ('text', 'image', 'audio', 'location'):
            return jsonify({'status': 'error', 'message': '不支持的消息类型'}), 400
        if msg_type == 'text' and not content:
            return jsonify({'status': 'error', 'message': '消息不能为空'}), 400
        check_text = content or (media_meta.get('place') if isinstance(media_meta, dict) else '') or ''
        hit = match_sensitive(check_text, 'message')
        if hit:
            return jsonify({'status': 'error', 'message': f'消息含敏感词「{hit}」'}), 400
        if msg_type in ('image', 'audio') and not media_url:
            return jsonify({'status': 'error', 'message': '请先上传媒体文件'}), 400
        if msg_type == 'location':
            if not content and not (isinstance(media_meta, dict) and media_meta.get('place')):
                return jsonify({'status': 'error', 'message': '请填写位置信息'}), 400
            if isinstance(media_meta, dict) and media_meta.get('place') and not content:
                content = str(media_meta.get('place'))
        if len(content) > 2000:
            return jsonify({'status': 'error', 'message': '消息过长'}), 400
        now = time.strftime('%Y-%m-%d %H:%M:%S')
        meta_str = ''
        if media_meta is not None:
            meta_str = json.dumps(media_meta, ensure_ascii=False) if isinstance(media_meta, dict) else str(media_meta)
        msg = Message(
            id=generate_id(),
            conversation_id=str(conv_id),
            sender_id=uid,
            sender_name=session.get('username', ''),
            msg_type=msg_type,
            content=content,
            media_url=media_url,
            media_meta=meta_str,
            is_read=False,
            created_at=now
        )
        db.session.add(msg)
        conv.last_preview = _message_preview(msg_type, content, media_url)
        conv.updated_at = now
        db.session.commit()
        d = msg.to_dict()
        push_chat_event(str(conv_id), {'type': 'new_message', 'conv_id': str(conv_id), 'message': d}, exclude_user=uid)
        peer = conv.peer_id_for(uid)
        push_notification(peer, 'message', '新私信', conv.last_preview, f'/messages?conv={conv.id}')
        db.session.commit()
        return jsonify({'status': 'success', 'message': d})


    @app.route('/api/conversations/<conv_id>/messages/<msg_id>/recall', methods=['POST'])
    def recall_message(conv_id, msg_id):
        """2 分钟内撤回消息"""
        if not is_logged_in():
            return jsonify({'status': 'error', 'message': '请先登录'}), 401
        uid = str(session['user_id'])
        conv = Conversation.query.filter_by(id=str(conv_id)).first()
        if not conv or uid not in (conv.user_a_id, conv.user_b_id):
            return jsonify({'status': 'error', 'message': '会话不存在或无权访问'}), 403
        msg = Message.query.filter_by(id=str(msg_id), conversation_id=str(conv_id)).first()
        if not msg:
            return jsonify({'status': 'error', 'message': '消息不存在'}), 404
        if str(msg.sender_id) != uid:
            return jsonify({'status': 'error', 'message': '只能撤回自己发送的消息'}), 403
        if msg.is_recalled:
            return jsonify({'status': 'success', 'message': msg.to_dict()})
        if msg.msg_type in ('system', 'appointment'):
            return jsonify({'status': 'error', 'message': '该类型消息不可撤回'}), 400
        try:
            ts = msg.created_at[:19]
            sent = datetime.strptime(ts, '%Y-%m-%d %H:%M:%S')
            if datetime.now() - sent > timedelta(minutes=2):
                return jsonify({'status': 'error', 'message': '超过2分钟无法撤回'}), 400
        except (ValueError, TypeError):
            pass
        now = time.strftime('%Y-%m-%d %H:%M:%S')
        msg.is_recalled = True
        msg.recalled_at = now
        msg.content = ''
        msg.media_url = ''
        msg.media_meta = ''
        conv.last_preview = '[消息已撤回]'
        conv.updated_at = now
        db.session.commit()
        d = msg.to_dict()
        push_chat_event(str(conv_id), {'type': 'recall', 'conv_id': str(conv_id), 'message': d})
        return jsonify({'status': 'success', 'message': d})


    @app.route('/api/conversations/<conv_id>/appointments', methods=['POST'])
    def create_appointment(conv_id):
        """面交预约；appointment_conflict 检测时间冲突"""
        if not is_logged_in():
            return jsonify({'status': 'error', 'message': '请先登录'}), 401
        uid = str(session['user_id'])
        conv = Conversation.query.filter_by(id=str(conv_id)).first()
        if not conv or uid not in (conv.user_a_id, conv.user_b_id):
            return jsonify({'status': 'error', 'message': '会话不存在或无权访问'}), 403
        data = request.json or {}
        place = (data.get('place') or '').strip()
        meeting_time = (data.get('meeting_time') or '').strip()
        if not place or not meeting_time:
            return jsonify({'status': 'error', 'message': '请填写面交地点和时间'}), 400
        proposer = User.query.filter_by(id=uid).first()
        if proposer and int(proposer.no_show_count or 0) >= 3:
            return jsonify({'status': 'error', 'message': '爽约次数过多，暂不可发起面交预约'}), 403
        conflict = appointment_conflict(uid, meeting_time)
        if conflict:
            return jsonify({
                'status': 'error',
                'message': f'该时段与已有预约冲突：{conflict.place} {conflict.meeting_time}',
                'conflict': conflict.to_dict()
            }), 409
        now = time.strftime('%Y-%m-%d %H:%M:%S')
        appt = MeetingAppointment(
            id=generate_id(),
            conversation_id=str(conv_id),
            order_id=str(data.get('order_id') or conv.order_id or ''),
            book_id=str(data.get('book_id') or conv.book_id or ''),
            proposer_id=uid,
            place=place,
            meeting_time=meeting_time,
            note=(data.get('note') or '').strip(),
            status='pending',
            created_at=now,
            updated_at=now
        )
        db.session.add(appt)
        preview = f'[面交预约] {place} {meeting_time}'
        msg = Message(
            id=generate_id(),
            conversation_id=str(conv_id),
            sender_id=uid,
            sender_name=session.get('username', ''),
            msg_type='appointment',
            content=preview,
            appointment_id=appt.id,
            is_read=False,
            created_at=now
        )
        db.session.add(msg)
        conv.last_preview = preview[:200]
        conv.updated_at = now
        peer = conv.peer_id_for(uid)
        push_notification(peer, 'appointment', '新的面交预约',
                          f'{session.get("username")} 提议 {place} {meeting_time}',
                          f'/messages?conv={conv.id}')
        db.session.commit()
        d = msg.to_dict(appt)
        push_chat_event(str(conv_id), {'type': 'new_message', 'conv_id': str(conv_id), 'message': d}, exclude_user=uid)
        return jsonify({'status': 'success', 'appointment': appt.to_dict(), 'message': d})


    @app.route('/api/appointments/<appt_id>/status', methods=['PUT'])
    def update_appointment_status(appt_id):
        """确认/取消面约；确认后订单→pickup"""
        if not is_logged_in():
            return jsonify({'status': 'error', 'message': '请先登录'}), 401
        uid = str(session['user_id'])
        appt = MeetingAppointment.query.filter_by(id=str(appt_id)).first()
        if not appt:
            return jsonify({'status': 'error', 'message': '预约不存在'}), 404
        conv = Conversation.query.filter_by(id=appt.conversation_id).first()
        if not conv or uid not in (conv.user_a_id, conv.user_b_id):
            return jsonify({'status': 'error', 'message': '无权操作'}), 403
        data = request.json or {}
        new_status = data.get('status', '')
        if new_status not in ('confirmed', 'cancelled'):
            return jsonify({'status': 'error', 'message': '无效状态'}), 400
        if str(appt.proposer_id) == uid and new_status == 'confirmed':
            return jsonify({'status': 'error', 'message': '需对方确认预约'}), 400
        if new_status == 'confirmed':
            conflict = appointment_conflict(uid, appt.meeting_time, exclude_id=appt.id)
            if conflict:
                return jsonify({
                    'status': 'error',
                    'message': f'确认失败：时段与预约 {conflict.place} {conflict.meeting_time} 冲突'
                }), 409
        appt.status = new_status
        appt.updated_at = time.strftime('%Y-%m-%d %H:%M:%S')
        if new_status == 'cancelled' and (data.get('no_show') or data.get('reason') == 'no_show'):
            target = User.query.filter_by(id=str(appt.proposer_id)).first()
            if target and str(target.id) != uid:
                target.no_show_count = int(target.no_show_count or 0) + 1
        label = '已确认' if new_status == 'confirmed' else '已取消'
        sys_msg = Message(
            id=generate_id(),
            conversation_id=appt.conversation_id,
            sender_id=uid,
            sender_name=session.get('username', ''),
            msg_type='system',
            content=f'[系统] 面交预约{label}：{appt.place} {appt.meeting_time}',
            is_read=False,
            created_at=appt.updated_at
        )
        db.session.add(sys_msg)
        conv.last_preview = sys_msg.content[:200]
        conv.updated_at = appt.updated_at
        if new_status == 'confirmed' and appt.order_id:
            order = Order.query.filter_by(id=str(appt.order_id)).first()
            if order and order.status == 'pending':
                order.status = 'pickup'
        peer = conv.peer_id_for(uid)
        push_notification(peer, 'appointment', f'面交预约{label}',
                          f'{appt.place} {appt.meeting_time}', f'/messages?conv={conv.id}')
        db.session.commit()
        sd = sys_msg.to_dict()
        push_chat_event(appt.conversation_id, {'type': 'new_message', 'conv_id': appt.conversation_id, 'message': sd}, exclude_user=uid)
        return jsonify({'status': 'success', 'appointment': appt.to_dict()})


    @app.route('/api/messages/unread', methods=['GET'])
    def unread_count():
        """私信未读总数"""
        if not is_logged_in():
            return jsonify({'status': 'error', 'message': '请先登录'}), 401
        uid = str(session['user_id'])
        conv_ids = [c.id for c in Conversation.query.filter(
            db.or_(Conversation.user_a_id == uid, Conversation.user_b_id == uid)
        ).all()]
        if not conv_ids:
            return jsonify({'status': 'success', 'unread_total': 0})
        count = Message.query.filter(
            Message.conversation_id.in_(conv_ids),
            Message.sender_id != uid,
            Message.is_read == False
        ).count()
        return jsonify({'status': 'success', 'unread_total': count})


    # ========== 交易体验：议价 / 通知 / 卖家主页 / 关注 / 相似推荐 ==========
    @app.route('/api/offers', methods=['GET'])
    def list_offers():
        """议价列表（buyer/seller 角色筛选）"""
        if not is_logged_in():
            return jsonify({'status': 'error', 'message': '请先登录'}), 401
        uid = str(session['user_id'])
        book_id = request.args.get('book_id')
        role = request.args.get('role')  # buyer / seller
        q = PriceOffer.query
        if book_id:
            q = q.filter_by(book_id=str(book_id))
        if role == 'seller':
            q = q.filter_by(seller_id=uid)
        elif role == 'buyer':
            q = q.filter_by(buyer_id=uid)
        else:
            q = q.filter(db.or_(PriceOffer.buyer_id == uid, PriceOffer.seller_id == uid))
        rows = q.order_by(PriceOffer.created_at.desc()).all()
        return jsonify({'status': 'success', 'offers': [o.to_dict() for o in rows]})


    @app.route('/api/offers', methods=['POST'])
    def create_offer():
        """买家对书籍出价议价"""
        if not is_logged_in():
            return jsonify({'status': 'error', 'message': '请先登录'}), 401
        data = request.json or {}
        book_id = str(data.get('book_id', ''))
        offer_price = float(data.get('offer_price', 0))
        if not book_id or offer_price <= 0:
            return jsonify({'status': 'error', 'message': '参数无效'}), 400
        book = Book.query.filter_by(id=book_id).first()
        if not book or book.status != 'available':
            return jsonify({'status': 'error', 'message': '书籍不可议价'}), 400
        seller_id = str(book.owner_id or '')
        buyer_id = str(session['user_id'])
        if buyer_id == seller_id:
            return jsonify({'status': 'error', 'message': '不能对自己的书报价'}), 400
        if offer_price > float(book.price):
            return jsonify({'status': 'error', 'message': '报价不能高于标价'}), 400
        exists = PriceOffer.query.filter_by(
            book_id=book_id, buyer_id=buyer_id, status='pending'
        ).first()
        if exists:
            return jsonify({'status': 'error', 'message': '您已有待处理的报价'}), 400
        offer = PriceOffer(
            id=generate_id(),
            book_id=book_id,
            book_title=book.title,
            buyer_id=buyer_id,
            buyer_name=session.get('username', ''),
            seller_id=seller_id,
            offer_price=offer_price,
            list_price=float(book.price),
            message=(data.get('message') or '').strip(),
            status='pending',
            created_at=time.strftime('%Y-%m-%d %H:%M:%S')
        )
        db.session.add(offer)
        push_notification(seller_id, 'offer', '收到新的议价',
                          f'{session.get("username")} 对《{book.title}》报价 ¥{offer_price}',
                          f'/book/{book_id}')
        db.session.commit()
        return jsonify({'status': 'success', 'offer': offer.to_dict()})


    @app.route('/api/offers/<offer_id>', methods=['PUT'])
    def respond_offer(offer_id):
        """卖家 accept/reject；accept 生成订单并锁书"""
        if not is_logged_in():
            return jsonify({'status': 'error', 'message': '请先登录'}), 401
        offer = PriceOffer.query.filter_by(id=str(offer_id)).first()
        if not offer:
            return jsonify({'status': 'error', 'message': '报价不存在'}), 404
        uid = str(session['user_id'])
        if uid != str(offer.seller_id) and not is_admin():
            return jsonify({'status': 'error', 'message': '仅卖家可处理报价'}), 403
        action = (request.json or {}).get('action', '')
        if action not in ('accept', 'reject'):
            return jsonify({'status': 'error', 'message': '无效操作'}), 400
        if offer.status != 'pending':
            return jsonify({'status': 'error', 'message': '报价已处理'}), 400
        book = Book.query.filter_by(id=str(offer.book_id)).first()
        if not book or book.status != 'available':
            return jsonify({'status': 'error', 'message': '书籍已不可售'}), 400
        if action == 'reject':
            offer.status = 'rejected'
            push_notification(offer.buyer_id, 'offer', '议价未通过',
                              f'《{offer.book_title}》卖家拒绝了您的报价', f'/book/{offer.book_id}')
            db.session.commit()
            return jsonify({'status': 'success', 'offer': offer.to_dict()})
        offer.status = 'accepted'
        new_order = Order(
            id=generate_id(),
            book_id=str(book.id),
            book_title=book.title,
            buyer_id=str(offer.buyer_id),
            buyer_name=offer.buyer_name,
            seller_id=str(offer.seller_id),
            seller_name=book.owner_name or book.seller or '',
            price=float(offer.offer_price),
            status='pending',
            created_at=time.strftime('%Y-%m-%d %H:%M:%S')
        )
        book.status = 'sold'
        db.session.add(new_order)
        PriceOffer.query.filter_by(book_id=str(book.id), status='pending').filter(
            PriceOffer.id != offer.id
        ).update({'status': 'cancelled'})
        push_notification(offer.buyer_id, 'offer', '议价成功',
                          f'《{book.title}》已按 ¥{offer.offer_price} 生成订单', f'/order/{new_order.id}')
        push_notification(offer.seller_id, 'order', '议价订单已生成',
                          f'买家 {offer.buyer_name} 以 ¥{offer.offer_price} 下单', f'/order/{new_order.id}')
        db.session.commit()
        return jsonify({'status': 'success', 'offer': offer.to_dict(), 'order': new_order.to_dict()})


    @app.route('/api/notifications', methods=['GET'])
    def list_notifications():
        """站内通知列表（降价、求购匹配等）"""
        if not is_logged_in():
            return jsonify({'status': 'error', 'message': '请先登录'}), 401
        uid = str(session['user_id'])
        rows = Notification.query.filter_by(user_id=uid).order_by(
            Notification.created_at.desc()
        ).limit(100).all()
        unread = Notification.query.filter_by(user_id=uid, is_read=False).count()
        return jsonify({
            'status': 'success',
            'notifications': [n.to_dict() for n in rows],
            'unread_count': unread
        })


    @app.route('/api/notifications/<nid>/read', methods=['PUT'])
    def read_notification(nid):
        """单条通知已读"""
        if not is_logged_in():
            return jsonify({'status': 'error', 'message': '请先登录'}), 401
        n = Notification.query.filter_by(id=str(nid), user_id=str(session['user_id'])).first()
        if n:
            n.is_read = True
            db.session.commit()
        return jsonify({'status': 'success'})


    @app.route('/api/notifications/read-all', methods=['PUT'])
    def read_all_notifications():
        """全部通知已读"""
        if not is_logged_in():
            return jsonify({'status': 'error', 'message': '请先登录'}), 401
        Notification.query.filter_by(user_id=str(session['user_id']), is_read=False).update(
            {'is_read': True}
        )
        db.session.commit()
        return jsonify({'status': 'success'})


    @app.route('/api/notifications/unread-count', methods=['GET'])
    def notification_unread_count():
        """站内通知未读数"""
        if not is_logged_in():
            return jsonify({'status': 'error', 'message': '请先登录'}), 401
        count = Notification.query.filter_by(
            user_id=str(session['user_id']), is_read=False
        ).count()
        return jsonify({'status': 'success', 'unread_count': count})


    @app.route('/api/sellers/<seller_id>', methods=['GET'])
    def seller_profile(seller_id):
        """卖家主页：在售书 + stats + 是否已关注"""
        user = User.query.filter_by(id=str(seller_id)).first()
        if not user:
            return jsonify({'status': 'error', 'message': '用户不存在'}), 404
        books = Book.query.filter_by(owner_id=str(seller_id), status='available').order_by(
            Book.created_at.desc()
        ).all()
        stats = seller_profile_stats(seller_id)
        following = False
        if is_logged_in():
            following = UserFollow.query.filter_by(
                follower_id=str(session['user_id']), seller_id=str(seller_id)
            ).first() is not None
        return jsonify({
            'status': 'success',
            'seller': user.to_dict(),
            'books': [b.to_dict() for b in books],
            'stats': stats,
            'is_following': following
        })


    @app.route('/api/follow/<seller_id>', methods=['POST'])
    def follow_seller(seller_id):
        """关注卖家（上新通知）"""
        if not is_logged_in():
            return jsonify({'status': 'error', 'message': '请先登录'}), 401
        fid = str(session['user_id'])
        sid = str(seller_id)
        if fid == sid:
            return jsonify({'status': 'error', 'message': '不能关注自己'}), 400
        if not User.query.filter_by(id=sid).first():
            return jsonify({'status': 'error', 'message': '用户不存在'}), 404
        if UserFollow.query.filter_by(follower_id=fid, seller_id=sid).first():
            return jsonify({'status': 'success', 'is_following': True})
        db.session.add(UserFollow(
            id=generate_id(), follower_id=fid, seller_id=sid,
            created_at=time.strftime('%Y-%m-%d %H:%M:%S')
        ))
        db.session.commit()
        return jsonify({'status': 'success', 'is_following': True})


    @app.route('/api/follow/<seller_id>', methods=['DELETE'])
    def unfollow_seller(seller_id):
        """取消关注"""
        if not is_logged_in():
            return jsonify({'status': 'error', 'message': '请先登录'}), 401
        row = UserFollow.query.filter_by(
            follower_id=str(session['user_id']), seller_id=str(seller_id)
        ).first()
        if row:
            db.session.delete(row)
            db.session.commit()
        return jsonify({'status': 'success', 'is_following': False})


    @app.route('/api/follow/check/<seller_id>', methods=['GET'])
    def check_follow(seller_id):
        """是否已关注该卖家"""
        if not is_logged_in():
            return jsonify({'status': 'success', 'is_following': False})
        row = UserFollow.query.filter_by(
            follower_id=str(session['user_id']), seller_id=str(seller_id)
        ).first()
        return jsonify({'status': 'success', 'is_following': row is not None})

