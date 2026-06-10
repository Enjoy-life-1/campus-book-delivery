"""订单 API：下单、列表、状态流转、CSV 导出、交易凭证"""
import csv
import time
from html import escape  # 凭证 HTML 防 XSS
from io import StringIO

from flask import jsonify, request, session, Response

from models import db, User, Book, Order


def orders_csv_response(orders, filename='orders.csv'):
    """将订单列表导出为 CSV 响应"""
    si = StringIO()
    w = csv.writer(si)
    w.writerow(['订单号', '类型', '书名', '买家', '卖家', '金额', '状态', '创建时间', '换书说明'])
    for o in orders:
        d = o.to_dict() if hasattr(o, 'to_dict') else o
        w.writerow([
            d.get('id', ''),
            '换书' if d.get('order_type') == 'exchange' else '购买',
            d.get('book_title', ''),
            d.get('buyer_name', ''),
            d.get('seller_name', ''),
            '' if d.get('order_type') == 'exchange' else d.get('price', ''),
            d.get('status', ''),
            d.get('created_at', ''),
            d.get('exchange_note', '') or d.get('exchange_book_title', '')
        ])
    return Response(
        '\ufeff' + si.getvalue(),  # BOM 便于 Excel 识别 UTF-8
        mimetype='text/csv; charset=utf-8',
        headers={'Content-Disposition': f'attachment; filename={filename}'}
    )


def register_orders_routes(app, helpers):
    """注册订单 CRUD、CSV 导出、HTML 凭证"""
    generate_id = helpers['generate_id']
    is_logged_in = helpers['is_logged_in']
    is_admin = helpers['is_admin']
    push_notification = helpers['push_notification']

    @app.route('/api/orders', methods=['POST'])
    def create_order():
        """立即购买：创建订单并将书籍 status 设为 sold"""
        if not is_logged_in():
            return jsonify({'status': 'error', 'message': '请先登录'}), 401

        data = request.json
        book = Book.query.filter_by(id=str(data.get('book_id', ''))).first()

        if not book:
            return jsonify({'status': 'error', 'message': '书籍不存在'}), 404

        if book.status != 'available':
            return jsonify({'status': 'error', 'message': '书籍已售出'}), 400

        owner_id = str(book.owner_id or book.sellerId or '')
        if owner_id == str(session['user_id']):
            return jsonify({'status': 'error', 'message': '不能购买自己的书籍'}), 400

        new_order = Order(
            id=generate_id(),
            book_id=str(book.id),
            book_title=book.title,
            buyer_id=str(session['user_id']),
            buyer_name=session.get('username', ''),
            seller_id=owner_id,
            seller_name=book.owner_name or book.seller or '',
            price=float(book.price),
            status='pending',  # 待面交
            created_at=time.strftime('%Y-%m-%d %H:%M:%S')
        )

        db.session.add(new_order)
        book.status = 'sold'  # 锁定库存
        push_notification(owner_id, 'order', '您有新的订单',
                          f'{session.get("username")} 下单《{book.title}》¥{book.price}',
                          f'/order/{new_order.id}')
        push_notification(str(session['user_id']), 'order', '订单已创建',
                          f'《{book.title}》待与卖家约定面交', f'/order/{new_order.id}')
        db.session.commit()

        return jsonify({'status': 'success', 'message': '订单创建成功', 'order': new_order.to_dict()})

    @app.route('/api/orders', methods=['GET'])
    def get_orders():
        """我的订单：admin 看全部，普通用户看买卖双方的"""
        if not is_logged_in():
            return jsonify({'status': 'error', 'message': '请先登录'}), 401

        user_id = str(session['user_id'])

        if is_admin():
            orders = [order.to_dict() for order in Order.query.all()]
        else:
            orders = [order.to_dict() for order in Order.query.filter(
                db.or_(Order.buyer_id == user_id, Order.seller_id == user_id)
            ).all()]

        return jsonify({'status': 'success', 'orders': orders})

    @app.route('/api/orders/export', methods=['GET'])
    def export_my_orders_csv():
        """导出当前用户相关订单 CSV"""
        if not is_logged_in():
            return jsonify({'status': 'error', 'message': '请先登录'}), 401
        user_id = str(session['user_id'])
        orders = Order.query.filter(
            db.or_(Order.buyer_id == user_id, Order.seller_id == user_id)
        ).order_by(Order.created_at.desc()).all()
        return orders_csv_response(orders, 'my_orders.csv')

    @app.route('/api/orders/<order_id>', methods=['GET'])
    def get_order_detail(order_id):
        """订单详情：仅买卖双方或 admin"""
        if not is_logged_in():
            return jsonify({'status': 'error', 'message': '请先登录'}), 401

        order = Order.query.filter_by(id=str(order_id)).first()

        if not order:
            return jsonify({'status': 'error', 'message': '订单不存在'}), 404

        user_id = str(session['user_id'])
        order_buyer_id = str(order.buyer_id or '')
        order_seller_id = str(order.seller_id or '')

        if not is_admin() and user_id != order_buyer_id and user_id != order_seller_id:
            return jsonify({'status': 'error', 'message': '无权查看此订单'}), 403

        return jsonify({'status': 'success', 'order': order.to_dict()})

    @app.route('/api/orders/<order_id>/voucher', methods=['GET'])
    def order_voucher(order_id):
        """已完成订单的可打印 HTML 交易凭证"""
        if not is_logged_in():
            return jsonify({'status': 'error', 'message': '请先登录'}), 401
        order = Order.query.filter_by(id=str(order_id)).first()
        if not order:
            return jsonify({'status': 'error', 'message': '订单不存在'}), 404
        user_id = str(session['user_id'])
        if not is_admin() and user_id not in (str(order.buyer_id or ''), str(order.seller_id or '')):
            return jsonify({'status': 'error', 'message': '无权查看此凭证'}), 403
        if order.status != 'completed':
            return jsonify({'status': 'error', 'message': '仅已完成订单可导出凭证'}), 400
        oid = escape(str(order.id))
        title = escape(order.book_title or '')
        buyer = escape(order.buyer_name or '')
        seller = escape(order.seller_name or '')
        created = escape(order.created_at or '')
        otype = order.order_type or 'sale'
        if otype == 'exchange':
            amount_line = f'<p><strong>类型：</strong>换书 · {escape(order.exchange_book_title or "")}</p>'
        else:
            amount_line = f'<p><strong>成交金额：</strong>¥{float(order.price or 0):.2f}</p>'
        html = f'''<!DOCTYPE html>
    <html lang="zh-CN"><head><meta charset="utf-8"><title>交易凭证 #{oid}</title>
    <style>
    body{{font-family:"Microsoft YaHei",sans-serif;max-width:720px;margin:40px auto;padding:24px;color:#222}}
    h1{{font-size:22px;border-bottom:2px solid #28a745;padding-bottom:8px}}
    .meta p{{margin:6px 0}} .stamp{{color:#28a745;font-weight:bold;margin-top:24px}}
    @media print{{.no-print{{display:none}}}}
    </style></head><body>
    <h1>校园书递 · 交易凭证</h1>
    <div class="meta">
    <p><strong>订单号：</strong>{oid}</p>
    <p><strong>书籍：</strong>{title}</p>
    {amount_line}
    <p><strong>买家：</strong>{buyer}</p>
    <p><strong>卖家：</strong>{seller}</p>
    <p><strong>完成时间：</strong>{created}</p>
    <p class="stamp">状态：面交已完成</p>
    </div>
    <p class="no-print"><button onclick="window.print()">打印 / 另存为 PDF</button></p>
    <p style="font-size:12px;color:#888">本凭证由校园书递平台生成，仅供校内二手教材交易留存。</p>
    </body></html>'''
        return Response(html, mimetype='text/html; charset=utf-8')

    @app.route('/api/orders/<order_id>/status', methods=['PUT'])
    def update_order_status(order_id):
        """面交流程：pending → pickup → completed / cancelled"""
        if not is_logged_in():
            return jsonify({'status': 'error', 'message': '请先登录'}), 401

        order = Order.query.filter_by(id=str(order_id)).first()

        if not order:
            return jsonify({'status': 'error', 'message': '订单不存在'}), 404

        user_id = str(session['user_id'])
        order_buyer_id = str(order.buyer_id or '')
        order_seller_id = str(order.seller_id or '')

        if not is_admin() and user_id != order_buyer_id and user_id != order_seller_id:
            return jsonify({'status': 'error', 'message': '无权操作此订单'}), 403

        data = request.json
        new_status = data.get('status')

        current_status = order.status or 'pending'
        if new_status == 'shipped':
            new_status = 'pickup'  # 兼容旧字段

        valid_transitions = {
            # 状态机：卖家确认 pickup，买家确认 completed
            'pending': ['pickup', 'cancelled'],
            'pickup': ['completed', 'cancelled'],
            'shipped': ['completed'],
            'completed': [],
            'cancelled': []
        }

        if new_status not in valid_transitions.get(current_status, []):
            return jsonify({'status': 'error', 'message': '无效的状态转换'}), 400

        if new_status == 'pickup' and user_id != order_seller_id and not is_admin():
            return jsonify({'status': 'error', 'message': '只有卖家可确认已约定面交'}), 403

        if new_status == 'completed' and user_id != order_buyer_id and not is_admin():
            return jsonify({'status': 'error', 'message': '只有买家可确认面交完成'}), 403

        cancel_reason = (data.get('cancel_reason') or '').strip()
        if new_status == 'cancelled' and cancel_reason:
            order.cancel_reason = cancel_reason[:300]
        order.status = new_status
        status_msgs = {
            'pickup': ('订单进度', '已约定面交，请按时赴约'),
            'completed': ('订单完成', '面交已完成，欢迎评价'),
            'cancelled': ('订单取消', cancel_reason or '订单已取消')
        }
        if new_status in status_msgs:
            title, body = status_msgs[new_status]
            for uid in (order_buyer_id, order_seller_id):
                push_notification(uid, 'order', title, f'《{order.book_title}》{body}', f'/order/{order.id}')
        if new_status == 'completed':
            for uid in (order_buyer_id, order_seller_id):
                push_notification(uid, 'review', '待评价提醒',
                                  f'订单《{order.book_title}》已完成，快来评价吧', f'/order/{order.id}')
        db.session.commit()

        return jsonify({'status': 'success', 'message': '订单状态更新成功', 'order': order.to_dict()})
