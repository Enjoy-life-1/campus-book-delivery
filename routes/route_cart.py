"""购物车 API：增删改查、同卖家合单结算、面交预约"""
import time

from flask import jsonify, request, session

from models import db, User, Book, Order, CartItem, Message, MeetingAppointment


def register_cart_routes(app, helpers):
    """注册购物车 CRUD + 同卖家结算"""
    generate_id = helpers['generate_id']
    is_logged_in = helpers['is_logged_in']
    push_notification = helpers['push_notification']
    get_or_create_conversation = helpers['get_or_create_conversation']
    appointment_conflict = helpers['appointment_conflict']  # 面交时间冲突检测

    @app.route('/api/cart', methods=['GET'])
    def get_cart():
        """获取购物车，附带书籍摘要信息"""
        if 'user_id' not in session:
            return jsonify({'status': 'error', 'message': '请先登录'}), 401

        user_id = str(session['user_id'])
        user_cart = CartItem.query.filter_by(user_id=user_id).all()

        cart_items = []
        for item in user_cart:
            item_dict = item.to_dict()
            book = Book.query.filter_by(id=str(item.book_id)).first()
            if book:
                book_dict = book.to_dict()
                item_dict['book'] = {  # 前端展示用精简字段
                    'id': book_dict['id'],
                    'title': book_dict.get('title', ''),
                    'author': book_dict.get('author', ''),
                    'price': book_dict.get('price', 0),
                    'cover_url': book_dict.get('cover_url') or (book_dict.get('imgs', [])[0] if book_dict.get('imgs') else '') or book_dict.get('image', ''),
                    'status': book_dict.get('status', 'available'),
                    'owner_id': book_dict.get('owner_id') or book_dict.get('sellerId') or '',
                    'owner_name': book_dict.get('owner_name') or book_dict.get('seller') or ''
                }
            cart_items.append(item_dict)

        return jsonify({'status': 'success', 'cart': cart_items})

    @app.route('/api/cart', methods=['POST'])
    def add_to_cart():
        """加入购物车，已存在则 quantity+1（上限 10）"""
        if 'user_id' not in session:
            return jsonify({'status': 'error', 'message': '请先登录'}), 401

        data = request.json
        book_id = data.get('book_id')
        quantity = int(data.get('quantity', 1))

        if not book_id:
            return jsonify({'status': 'error', 'message': '书籍ID不能为空'}), 400

        book = Book.query.filter_by(id=str(book_id)).first()
        if not book:
            return jsonify({'status': 'error', 'message': '书籍不存在'}), 404

        if book.status != 'available':
            return jsonify({'status': 'error', 'message': '该书籍暂不可购买'}), 400

        owner_id = str(book.owner_id or book.sellerId or '')
        if owner_id == str(session['user_id']):
            return jsonify({'status': 'error', 'message': '不能添加自己发布的书籍到购物车'}), 400

        user_id = str(session['user_id'])
        book_id_str = str(book_id)

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

    @app.route('/api/cart/checkout-seller', methods=['POST'])
    def checkout_cart_seller():
        """同卖家合单：批量创建订单、删购物车项、可选面交预约"""
        if not is_logged_in():
            return jsonify({'status': 'error', 'message': '请先登录'}), 401
        data = request.json or {}
        seller_id = str(data.get('seller_id') or '').strip()
        item_ids = [str(x) for x in (data.get('cart_item_ids') or []) if x]
        place = (data.get('place') or '').strip()
        meeting_time = (data.get('meeting_time') or '').strip()
        note = (data.get('note') or '').strip()
        if not seller_id:
            return jsonify({'status': 'error', 'message': '缺少卖家信息'}), 400
        if not item_ids:
            return jsonify({'status': 'error', 'message': '请选择要结算的商品'}), 400
        uid = str(session['user_id'])
        if seller_id == uid:
            return jsonify({'status': 'error', 'message': '不能购买自己的书籍'}), 400
        seller = User.query.filter_by(id=seller_id).first()
        if not seller:
            return jsonify({'status': 'error', 'message': '卖家不存在'}), 404
        rows = CartItem.query.filter(
            CartItem.user_id == uid,
            CartItem.id.in_(item_ids)
        ).all()
        if not rows:
            return jsonify({'status': 'error', 'message': '购物车商品不存在'}), 404
        orders = []
        titles = []
        for item in rows:
            book = Book.query.filter_by(id=str(item.book_id)).first()
            if not book:
                continue
            owner_id = str(book.owner_id or book.sellerId or '')
            if owner_id != seller_id:
                return jsonify({'status': 'error', 'message': '所选商品须为同一卖家'}), 400
            if book.status != 'available':
                return jsonify({'status': 'error', 'message': f'《{book.title}》已不可购买'}), 400
            oid = generate_id()
            order = Order(
                id=oid,
                book_id=str(book.id),
                book_title=book.title,
                buyer_id=uid,
                buyer_name=session.get('username', ''),
                seller_id=seller_id,
                seller_name=book.owner_name or book.seller or seller.username,
                price=float(book.price),
                status='pending',
                created_at=time.strftime('%Y-%m-%d %H:%M:%S')
            )
            db.session.add(order)
            book.status = 'sold'  # 锁定库存
            orders.append(order)
            titles.append(book.title)
            push_notification(seller_id, 'order', '您有新的订单',
                              f'{session.get("username")} 下单《{book.title}》¥{book.price}',
                              f'/order/{oid}')
            db.session.delete(item)  # 结算后移除购物车
        if not orders:
            return jsonify({'status': 'error', 'message': '没有可结算的商品'}), 400
        first = orders[0]
        batch_title = f'合单{len(orders)}本：' + '、'.join(titles[:3]) + ('…' if len(titles) > 3 else '')
        conv = get_or_create_conversation(  # 创建私信会话
            uid, seller_id, first.book_id, first.id, batch_title
        )
        appointment = None
        if place and meeting_time:
            conflict = appointment_conflict(uid, meeting_time)
            if conflict:
                db.session.rollback()
                return jsonify({
                    'status': 'error',
                    'message': f'该时段与已有预约冲突：{conflict.place} {conflict.meeting_time}'
                }), 409
            now = time.strftime('%Y-%m-%d %H:%M:%S')
            order_ids = ','.join(o.id for o in orders)
            appt_note = (note + '；' if note else '') + f'购物车合单，订单：{order_ids}'
            appt = MeetingAppointment(
                id=generate_id(),
                conversation_id=str(conv.id),
                order_id=first.id,
                book_id=first.book_id or '',
                proposer_id=uid,
                place=place,
                meeting_time=meeting_time,
                note=appt_note[:500],
                status='pending',
                created_at=now,
                updated_at=now
            )
            db.session.add(appt)
            preview = f'[合单面交预约] {place} {meeting_time}（{len(orders)}单）'
            msg = Message(
                id=generate_id(),
                conversation_id=str(conv.id),
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
            appointment = appt.to_dict()
            peer = conv.peer_id_for(uid)
            push_notification(peer, 'appointment', '新的合单面交预约',
                              f'{session.get("username")} 提议 {place} {meeting_time}（{len(orders)}单）',
                              f'/messages?conv={conv.id}')
        push_notification(uid, 'order', '合单下单成功',
                          f'已创建 {len(orders)} 笔订单，待面交', '/transactionHistory')
        db.session.commit()
        return jsonify({
            'status': 'success',
            'message': f'已创建 {len(orders)} 个订单' + ('并已发送面交预约' if appointment else ''),
            'orders': [o.to_dict() for o in orders],
            'conversation_id': conv.id,
            'appointment': appointment
        })

    @app.route('/api/cart/<item_id>', methods=['PUT'])
    def update_cart_item(item_id):
        """修改购物车数量（1-10）"""
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

    @app.route('/api/cart/<item_id>', methods=['DELETE'])
    def delete_cart_item(item_id):
        """删除单个购物车项"""
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

    @app.route('/api/cart', methods=['DELETE'])
    def clear_cart():
        """清空当前用户购物车"""
        if 'user_id' not in session:
            return jsonify({'status': 'error', 'message': '请先登录'}), 401

        CartItem.query.filter_by(user_id=str(session['user_id'])).delete()
        db.session.commit()

        return jsonify({'status': 'success', 'message': '购物车已清空'})
