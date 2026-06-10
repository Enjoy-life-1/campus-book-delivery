"""收藏/评论/评价/求购 API"""
import time

from flask import jsonify, request, session

from services.admin_compliance import match_sensitive
from models import db, User, Book, Order, Collection, Comment, Review, WantedPost


def register_community_routes(app, helpers):
    """注册收藏、评论、评价、求购 API"""
    generate_id = helpers['generate_id']
    is_logged_in = helpers['is_logged_in']
    is_admin = helpers['is_admin']
    is_full_admin = helpers['is_full_admin']
    find_wanted_matches = helpers['find_wanted_matches']
    push_notification = helpers['push_notification']
    app_ref = helpers.get('app') or app

    # 收藏相关API
    # 检查收藏状态
    @app.route('/api/collections/check/<book_id>', methods=['GET'])
    def check_collection(book_id):
        """检查当前用户是否已收藏该书"""
        if not is_logged_in():
            return jsonify({'status': 'error', 'message': '请先登录'}), 401
    
        user_id = str(session['user_id'])
        collection = Collection.query.filter_by(
            book_id=str(book_id),
            user_id=user_id
        ).first()
    
        return jsonify({
            'status': 'success',
            'is_collected': collection is not None
        })

    # 收藏/取消收藏
    @app.route('/api/collections/<book_id>', methods=['POST'])
    def toggle_collection(book_id):
        """切换收藏；新建时记录 collected_price 供降价对比"""
        if not is_logged_in():
            return jsonify({'status': 'error', 'message': '请先登录'}), 401
    
        user_id = str(session['user_id'])
        book_id_str = str(book_id)
    
        # 检查是否已收藏
        collection = Collection.query.filter_by(
            book_id=book_id_str,
            user_id=user_id
        ).first()
    
        if collection:
            # 取消收藏
            db.session.delete(collection)
            db.session.commit()
            return jsonify({'status': 'success', 'message': '取消收藏成功', 'is_collected': False})
    
        book = Book.query.filter_by(id=book_id_str).first()
        snap_price = float(book.price) if book and book.price else None
        new_collection = Collection(
            id=generate_id(),
            book_id=book_id_str,
            user_id=user_id,
            username=session.get('username', ''),
            collected_price=snap_price,
            price_alert=True,
            created_at=time.strftime('%Y-%m-%d %H:%M:%S')
        )
    
        db.session.add(new_collection)
        db.session.commit()
    
        return jsonify({'status': 'success', 'message': '收藏成功', 'is_collected': True})

    # 获取用户收藏列表
    @app.route('/api/collections', methods=['GET'])
    def get_collections():
        """收藏列表 + 降价标记"""
        if not is_logged_in():
            return jsonify({'status': 'error', 'message': '请先登录'}), 401
    
        user_id = str(session['user_id'])
        user_collections = Collection.query.filter_by(user_id=user_id).all()
    
        # 获取收藏的书籍详情
        collected_books = []
        for collection in user_collections:
            book = Book.query.filter_by(id=str(collection.book_id)).first()
            if book:
                d = book.to_dict()
                snap = collection.collected_price
                d['collected_price'] = float(snap) if snap is not None else None
                d['price_alert'] = collection.price_alert is not False
                if snap is not None and book.price is not None and float(book.price) < float(snap):
                    d['price_dropped_since_collect'] = True
                collected_books.append(d)

        return jsonify({'status': 'success', 'collections': collected_books, 'books': collected_books})

    # 评论相关 API（SQLite）
    @app.route('/api/comments/<book_id>', methods=['GET'])
    def get_comments(book_id):
        """已审核通过的评论列表"""
        try:
            rows = Comment.query.filter_by(
                book_id=str(book_id),
                is_deleted=False,
                audit_status='approved'
            ).order_by(Comment.created_at.desc()).all()
            return jsonify({'status': 'success', 'comments': [c.to_dict() for c in rows]})
        except Exception as e:
            print(f'获取评论列表错误: {e}')
            return jsonify({'status': 'error', 'message': f'服务器错误: {str(e)}'}), 500


    @app.route('/api/comments', methods=['POST'])
    def add_comment():
        """发表评论；敏感词过滤；非 full_admin 需审核 pending"""
        if not is_logged_in():
            return jsonify({'status': 'error', 'message': '请先登录'}), 401

        data = request.json or {}
        book_id = str(data.get('book_id', ''))
        content = (data.get('content') or '').strip()

        if not book_id:
            return jsonify({'status': 'error', 'message': '书籍ID不能为空'}), 400
        if not content:
            return jsonify({'status': 'error', 'message': '评论内容不能为空'}), 400
        if len(content) > 1000:
            return jsonify({'status': 'error', 'message': '评论内容不能超过1000字'}), 400

        book = Book.query.filter_by(id=book_id).first()
        if not book:
            return jsonify({'status': 'error', 'message': '书籍不存在'}), 404

        hit = match_sensitive(content, 'comment')
        if hit:
            return jsonify({'status': 'error', 'message': f'评论含敏感词「{hit}」，请修改后重试'}), 400

        try:
            audit_st = 'approved' if is_full_admin() else 'pending'
            new_comment = Comment(
                id=generate_id(),
                book_id=book_id,
                book_title=book.title,
                user_id=str(session['user_id']),
                username=session.get('username', '匿名用户'),
                content=content,
                likes=0,
                is_deleted=False,
                audit_status=audit_st,
                created_at=time.strftime('%Y-%m-%d %H:%M:%S')
            )
            db.session.add(new_comment)
            db.session.commit()
            msg = '评论发表成功' if audit_st == 'approved' else '评论已提交，审核通过后展示'
            return jsonify({
                'status': 'success',
                'message': msg,
                'comment': new_comment.to_dict()
            })
        except Exception as e:
            db.session.rollback()
            print(f'添加评论错误: {e}')
            return jsonify({'status': 'error', 'message': f'服务器错误: {str(e)}'}), 500


    @app.route('/api/comments/<comment_id>', methods=['DELETE'])
    def delete_comment(comment_id):
        """软删除评论（is_deleted）"""
        if not is_logged_in():
            return jsonify({'status': 'error', 'message': '请先登录'}), 401

        try:
            comment = Comment.query.filter_by(id=str(comment_id)).first()
            if not comment or comment.is_deleted:
                return jsonify({'status': 'error', 'message': '评论不存在'}), 404

            user_id = str(session['user_id'])
            if str(comment.user_id) != user_id and not is_admin():
                return jsonify({'status': 'error', 'message': '无权限删除此评论'}), 403

            comment.is_deleted = True
            db.session.commit()
            return jsonify({'status': 'success', 'message': '评论删除成功'})
        except Exception as e:
            db.session.rollback()
            print(f'删除评论错误: {e}')
            return jsonify({'status': 'error', 'message': f'服务器错误: {str(e)}'}), 500


    # 评价相关 API（SQLite）
    @app.route('/api/reviews', methods=['POST'])
    def submit_review():
        """订单完成后买卖双方互评，四维评分 1-5"""
        if not is_logged_in():
            return jsonify({'status': 'error', 'message': '请先登录'}), 401

        try:
            data = request.json or {}
            order_id = str(data.get('order_id', ''))
            reviewed_user_id = str(data.get('reviewed_user_id', ''))
            reviewer_role = data.get('reviewer_role', '')
            description_rating = int(data.get('description_rating') or data.get('desc_rating') or 0)
            service_rating = int(data.get('service_rating', 0))
            condition_rating = int(data.get('condition_rating', 0))
            efficiency_rating = int(data.get('efficiency_rating', 0))
            review_content = (data.get('review_content') or '').strip()
            if not description_rating:
                description_rating = service_rating or 5

            ratings = [description_rating, service_rating, condition_rating, efficiency_rating]
            if not all(1 <= rating <= 5 for rating in ratings):
                return jsonify({'status': 'error', 'message': '评分必须在1-5之间'}), 400

            order = Order.query.filter_by(id=order_id).first()
            if not order:
                return jsonify({'status': 'error', 'message': '订单不存在'}), 404
            if order.status != 'completed':
                return jsonify({'status': 'error', 'message': '只有已完成的订单才能评价'}), 400

            user_id = str(session['user_id'])
            if reviewer_role == 'buyer' and user_id != str(order.buyer_id or ''):
                return jsonify({'status': 'error', 'message': '只有买家可以评价卖家'}), 403
            if reviewer_role == 'seller' and user_id != str(order.seller_id or ''):
                return jsonify({'status': 'error', 'message': '只有卖家可以评价买家'}), 403

            if Review.query.filter_by(order_id=order_id, reviewer_id=user_id).first():
                return jsonify({'status': 'error', 'message': '您已经评价过此订单'}), 400

            review = Review(
                id=generate_id(),
                order_id=order_id,
                book_id=str(order.book_id or ''),
                reviewer_id=user_id,
                reviewer_name=session.get('username', ''),
                reviewer_role=reviewer_role,
                reviewed_user_id=reviewed_user_id,
                description_rating=description_rating,
                service_rating=service_rating,
                condition_rating=condition_rating,
                efficiency_rating=efficiency_rating,
                review_content=review_content,
                created_at=time.strftime('%Y-%m-%d %H:%M:%S')
            )
            db.session.add(review)
            db.session.commit()
            return jsonify({'status': 'success', 'message': '评价提交成功', 'review': review.to_dict()})
        except Exception as e:
            db.session.rollback()
            print(f'提交评价错误: {e}')
            return jsonify({'status': 'error', 'message': f'服务器错误: {str(e)}'}), 500


    @app.route('/api/reviews/order/<order_id>', methods=['GET'])
    def get_order_reviews(order_id):
        """订单双方评价"""
        if not is_logged_in():
            return jsonify({'status': 'error', 'message': '请先登录'}), 401

        try:
            order = Order.query.filter_by(id=str(order_id)).first()
            if not order:
                return jsonify({'status': 'error', 'message': '订单不存在'}), 404

            user_id = str(session['user_id'])
            if not is_admin() and user_id != str(order.buyer_id or '') and user_id != str(order.seller_id or ''):
                return jsonify({'status': 'error', 'message': '无权查看此订单的评价'}), 403

            rows = Review.query.filter_by(order_id=str(order_id)).order_by(Review.created_at.desc()).all()
            return jsonify({'status': 'success', 'reviews': [r.to_dict() for r in rows]})
        except Exception as e:
            print(f'获取评价错误: {e}')
            return jsonify({'status': 'error', 'message': f'服务器错误: {str(e)}'}), 500


    # ========== 求购匹配 ==========
    @app.route('/api/wanted', methods=['GET'])
    def list_wanted():
        """求购列表；mine=1 只看自己的；附带 match_count"""
        mine = request.args.get('mine') == '1'
        status = request.args.get('status', 'open')
        if mine:
            if not is_logged_in():
                return jsonify({'status': 'error', 'message': '请先登录'}), 401
            q = WantedPost.query.filter_by(user_id=str(session['user_id']))
            if status:
                q = q.filter_by(status=status)
            rows = q.order_by(WantedPost.created_at.desc()).all()
        else:
            q = WantedPost.query.filter_by(status='open')
            rows = q.order_by(WantedPost.created_at.desc()).all()
        items = []
        for w in rows:
            d = w.to_dict()
            d['match_count'] = len(find_wanted_matches(w))
            items.append(d)
        return jsonify({'status': 'success', 'wanted': items})


    @app.route('/api/wanted/<wanted_id>', methods=['GET'])
    def get_wanted(wanted_id):
        """求购详情 + 匹配书籍"""
        w = WantedPost.query.filter_by(id=str(wanted_id)).first()
        if not w:
            return jsonify({'status': 'error', 'message': '求购不存在'}), 404
        d = w.to_dict()
        d['matches'] = find_wanted_matches(w)
        d['match_count'] = len(d['matches'])
        return jsonify({'status': 'success', 'wanted': d})


    @app.route('/api/wanted', methods=['POST'])
    def create_wanted():
        """发布求购；有匹配则 push_notification"""
        if not is_logged_in():
            return jsonify({'status': 'error', 'message': '请先登录'}), 401
        data = request.json or {}
        title = (data.get('title') or '').strip()
        if not title:
            return jsonify({'status': 'error', 'message': '书名不能为空'}), 400
        w = WantedPost(
            id=generate_id(),
            user_id=str(session['user_id']),
            username=session.get('username', ''),
            title=title,
            author=(data.get('author') or '').strip(),
            isbn=(data.get('isbn') or '').strip(),
            category=data.get('category') or 'other',
            max_price=float(data['max_price']) if data.get('max_price') not in (None, '') else None,
            desc=(data.get('desc') or '').strip(),
            status='open',
            created_at=time.strftime('%Y-%m-%d %H:%M:%S')
        )
        db.session.add(w)
        db.session.commit()
        d = w.to_dict()
        d['matches'] = find_wanted_matches(w)
        d['match_count'] = len(d['matches'])
        if d['match_count']:
            push_notification(
                w.user_id, 'new_book', '求购已有匹配',
                f'《{w.title}》发现 {d["match_count"]} 本在售匹配书籍',
                f'/wanted/{w.id}'
            )
        return jsonify({'status': 'success', 'message': '求购发布成功', 'wanted': d})


    @app.route('/api/wanted/<wanted_id>', methods=['PUT'])
    def update_wanted(wanted_id):
        """编辑求购或关闭"""
        if not is_logged_in():
            return jsonify({'status': 'error', 'message': '请先登录'}), 401
        w = WantedPost.query.filter_by(id=str(wanted_id)).first()
        if not w:
            return jsonify({'status': 'error', 'message': '求购不存在'}), 404
        if str(w.user_id) != str(session['user_id']):
            return jsonify({'status': 'error', 'message': '无权限操作'}), 403
        data = request.json or {}
        if 'status' in data:
            w.status = data['status']
        for field in ('title', 'author', 'isbn', 'desc'):
            if field in data:
                setattr(w, field, (data[field] or '').strip())
        if 'max_price' in data:
            w.max_price = float(data['max_price']) if data['max_price'] not in (None, '') else None
        if 'category' in data:
            w.category = data['category']
        db.session.commit()
        d = w.to_dict()
        d['matches'] = find_wanted_matches(w)
        return jsonify({'status': 'success', 'wanted': d})


    @app.route('/api/wanted/<wanted_id>/matches', methods=['GET'])
    def wanted_matches(wanted_id):
        """求购匹配的在售书"""
        w = WantedPost.query.filter_by(id=str(wanted_id)).first()
        if not w:
            return jsonify({'status': 'error', 'message': '求购不存在'}), 404
        matches = find_wanted_matches(w)
        return jsonify({'status': 'success', 'matches': matches})


    @app.route('/api/wanted/<wanted_id>', methods=['DELETE'])
    def delete_wanted(wanted_id):
        """删除求购帖"""
        if not is_logged_in():
            return jsonify({'status': 'error', 'message': '请先登录'}), 401
        w = WantedPost.query.filter_by(id=str(wanted_id)).first()
        if not w:
            return jsonify({'status': 'error', 'message': '求购不存在'}), 404
        if str(w.user_id) != str(session['user_id']) and not is_admin():
            return jsonify({'status': 'error', 'message': '无权限删除'}), 403
        db.session.delete(w)
        db.session.commit()
        return jsonify({'status': 'success', 'message': '已删除'})


