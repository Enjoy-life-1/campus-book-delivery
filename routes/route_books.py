"""书籍 API：列表筛选、发布、编辑、删除、复制"""
import json
import os
import re
import time
import urllib.parse
import urllib.request
from datetime import datetime, timedelta

from flask import jsonify, request, session

from services.admin_compliance import isbn_blacklisted, user_ban_blocked
from services.book_media import normalize_book_images
from services.discovery_features import build_search_filter, merge_recommendations, price_insights, publish_hints
from models import db, User, Book, Collection, Setting
from services.seller_tools import apply_price_drop_ladders, record_book_view


def register_books_routes(app, helpers):
    """注册 /api/books 相关路由"""
    generate_id = helpers['generate_id']
    is_logged_in = helpers['is_logged_in']
    is_admin = helpers['is_admin']
    is_full_admin = helpers['is_full_admin']
    filter_books_campus = helpers['filter_books_campus']
    enrich_book_dict = helpers['enrich_book_dict']
    notify_price_drop = helpers['notify_price_drop']
    notify_seller_followers_new_book = helpers['notify_seller_followers_new_book']
    notify_wanted_match_for_book = helpers['notify_wanted_match_for_book']
    find_similar_books = helpers['find_similar_books']
    push_notification = helpers['push_notification']
    flask_app = helpers['app']

    # 书籍相关API
    # 获取书籍列表
    @app.route('/api/books', methods=['GET'])
    def get_books():
        """书籍列表：分类/搜索/排序/价格/校区筛选 + 分页"""
        apply_price_drop_ladders(notify_price_drop)  # 处理到期阶梯降价
        # 获取查询参数
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 1000))
        category = request.args.get('category')
        search = request.args.get('search', '').strip().lower()
        include_sold = request.args.get('include_sold', 'false').lower() == 'true'
        owner_id = request.args.get('owner_id')
    
        # 构建查询
        query = Book.query
    
        if owner_id and is_logged_in() and str(owner_id) == str(session.get('user_id')):
            query = query.filter_by(owner_id=str(owner_id))
        elif not include_sold and not is_admin():
            query = query.filter_by(status='available')
    
        # 分类筛选
        if category and category != 'all':
            query = query.filter_by(category=category)
    
        if search:
            sf = build_search_filter(search)
            if sf is not None:
                query = query.filter(sf)
    
        # 获取所有结果用于价格筛选和总数
        all_books = [book.to_dict() for book in query.all()]
    
        # 按创建时间降序排序（新发布的书籍显示在最前面）
        def get_sort_time(book):
            """获取书籍的排序时间，优先使用created_at，其次createTime，最后publish_date"""
            time_str = book.get('created_at') or book.get('createTime') or book.get('publish_date') or ''
            if not time_str:
                return '1970-01-01 00:00:00'  # 如果没有时间，排到最后
            # 如果时间格式不完整，尝试补充
            if len(time_str) == 10:  # 只有日期，没有时间
                time_str += ' 00:00:00'
            return time_str
    
        sort_by = request.args.get('sort_by', 'newest')
        if sort_by == 'oldest':
            all_books.sort(key=get_sort_time)
        elif sort_by == 'price_asc':
            all_books.sort(key=lambda b: float(b.get('price') or 0))
        elif sort_by == 'price_desc':
            all_books.sort(key=lambda b: float(b.get('price') or 0), reverse=True)
        elif sort_by == 'title':
            all_books.sort(key=lambda b: (b.get('title') or '').lower())
        else:
            all_books.sort(key=get_sort_time, reverse=True)

        # 发布时间筛选
        time_range = request.args.get('time_range') or request.args.get('timeRange')
        if time_range and time_range != 'all':
            now = datetime.now()
            filtered_by_time = []
            for book in all_books:
                time_str = book.get('created_at') or book.get('createTime') or book.get('publish_date') or ''
                if not time_str:
                    continue
                try:
                    if len(time_str) == 10:
                        book_dt = datetime.strptime(time_str, '%Y-%m-%d')
                    else:
                        book_dt = datetime.strptime(time_str[:19], '%Y-%m-%d %H:%M:%S')
                except ValueError:
                    continue
                if time_range == 'today' and book_dt.date() == now.date():
                    filtered_by_time.append(book)
                elif time_range == 'week' and book_dt >= now - timedelta(days=7):
                    filtered_by_time.append(book)
                elif time_range == 'month' and book_dt >= now - timedelta(days=30):
                    filtered_by_time.append(book)
            all_books = filtered_by_time
    
        # 价格范围筛选
        price_range = request.args.get('priceRange')
        if price_range and price_range != 'all':
            filtered_books = []
            for book in all_books:
                price = float(book.get('price', 0))
                if price_range == '0-50' and 0 <= price <= 50:
                    filtered_books.append(book)
                elif price_range == '50-100' and 50 < price <= 100:
                    filtered_books.append(book)
                elif price_range == '100+' and price > 100:
                    filtered_books.append(book)
            all_books = filtered_books

        all_books = filter_books_campus(all_books, request.args)
    
        # 分页
        start = (page - 1) * page_size
        end = start + page_size
        paginated_books = all_books[start:end]
    
        return jsonify({
            'status': 'success',
            'books': paginated_books,
            'total': len(all_books),
            'page': page,
            'page_size': page_size
        })

    # 获取书籍详情
    @app.route('/api/books/<book_id>', methods=['GET'])
    def get_book_detail(book_id):
        """书籍详情：浏览量、相似书、价格洞察、发布提示"""
        try:
            apply_price_drop_ladders(notify_price_drop)
            book = Book.query.filter_by(id=str(book_id)).first()
            if not book:
                return jsonify({'status': 'error', 'message': '书籍不存在'}), 404
            vid = session.get('user_id') if is_logged_in() else None
            record_book_view(book_id, vid)
            d = book.to_dict()
            owner = User.query.filter_by(id=str(book.owner_id or '')).first()
            enrich_book_dict(d, owner)
            uid = session.get('user_id') if is_logged_in() else None
            d['similar_books'] = merge_recommendations(find_similar_books, book, uid)
            d['price_insights'] = price_insights(book)
            hints = publish_hints({
                'isbn': d.get('isbn'), 'course_code': d.get('course_code'),
                'edition': d.get('edition'), 'title': d.get('title'), 'price': d.get('price'),
                'category': d.get('category')
            })
            d['course_hints'] = hints
            return jsonify({'status': 'success', 'book': d, 'similar_books': d['similar_books'], 'price_insights': d['price_insights']})
        except Exception as e:
            print(f'获取书籍详情错误: {e}')
            return jsonify({'status': 'error', 'message': f'服务器错误: {str(e)}'}), 500

    # 添加新书籍
    @app.route('/api/books', methods=['POST'])
    def add_book():
        """发布书籍：普通用户 pending 待审，full_admin 直接 available"""
        if not is_logged_in():
            return jsonify({'status': 'error', 'message': '请先登录'}), 401
    
        data = request.json
    
        # 验证必填字段
        if not data.get('title') or not data.get('title').strip():
            return jsonify({'status': 'error', 'message': '书籍标题不能为空'}), 400
    
        if not data.get('category'):
            return jsonify({'status': 'error', 'message': '请选择书籍分类'}), 400
    
        if not data.get('price') or float(data.get('price', 0)) <= 0:
            return jsonify({'status': 'error', 'message': '价格必须大于0'}), 400
    
        if not data.get('desc') or not data.get('desc').strip():
            return jsonify({'status': 'error', 'message': '请填写书籍描述'}), 400
    
        if not data.get('contact') or not data.get('contact').strip():
            return jsonify({'status': 'error', 'message': '请填写联系方式'}), 400

        isbn_val = (data.get('isbn') or '').strip()
        if isbn_val:
            bl = isbn_blacklisted(isbn_val)
            if bl:
                return jsonify({'status': 'error', 'message': f'该 ISBN 在违禁黑名单中：{bl.reason or "盗版/违禁"}'}), 400

        u = User.query.filter_by(id=str(session['user_id'])).first()
        ban_msg = user_ban_blocked(u)
        if ban_msg:
            return jsonify({'status': 'error', 'message': ban_msg}), 403

        # 处理图片
        imgs = data.get('imgs', [])
        if not imgs or len(imgs) == 0:
            return jsonify({'status': 'error', 'message': '请至少上传一张图片'}), 400
    
        if isinstance(imgs, str):
            imgs = [imgs]
        try:
            imgs = normalize_book_images(flask_app, imgs, generate_id)
        except ValueError as e:
            return jsonify({'status': 'error', 'message': str(e)}), 400
        if not imgs:
            return jsonify({'status': 'error', 'message': '请至少上传一张图片'}), 400

        user_id = str(session['user_id'])
        username = session.get('username', '')
        seller = User.query.filter_by(id=user_id).first()

        from services.campus_dorms import load_dorm_catalog, validate_dorm_zone
        book_zone = (data.get('campus_zone') or (seller.campus_zone if seller else '') or '西校区').strip()
        book_dorm = (data.get('dorm_building') or (seller.dorm_building if seller else '') or '').strip()
        _, by_zone, _ = load_dorm_catalog(Setting)
        ok, msg = validate_dorm_zone(book_dorm, book_zone, by_zone)
        if not ok:
            return jsonify({'status': 'error', 'message': msg}), 400
    
        # 创建新书籍对象
        new_book = Book(
            id=generate_id(),
            title=data['title'].strip(),
            author=data.get('author', '').strip() or '未知作者',
            category=data.get('category', 'other'),
            price=float(data.get('price', 0)),
            desc=data.get('desc', '').strip(),
            description=data.get('desc', '').strip(),
            imgs=json.dumps(imgs, ensure_ascii=False),
            image=imgs[0] if imgs else '',
            cover_url=imgs[0] if imgs else '',
            contact=data.get('contact', '').strip(),
            stock=int(data.get('stock', 1)),
            status='available' if is_full_admin() else 'pending',  # 非管理员需审核
            condition=data.get('condition', '').strip() or '',
            isbn=data.get('isbn', '').strip() or '',
            edition=(data.get('edition') or '').strip(),
            course_code=(data.get('course_code') or '').strip(),
            campus_zone=book_zone,
            dorm_building=book_dorm,
            school_id=(seller.school_id if seller else '') or '',
            campaign_tag=(data.get('campaign_tag') or '').strip(),
            original_price=float(data['original_price']) if data.get('original_price') not in (None, '') else None,
            price_drop_until=(data.get('price_drop_until') or '').strip(),
            listing_type=(data.get('listing_type') or 'single').strip(),
            bundle_items=json.dumps(data.get('bundle_items') or [], ensure_ascii=False),
            owner_id=user_id,
            owner_name=username,
            seller=username,
            sellerId=user_id,
            createTime=time.strftime('%Y-%m-%d'),
            created_at=time.strftime('%Y-%m-%d %H:%M:%S'),
            publish_date=time.strftime('%Y-%m-%d')
        )
    
        db.session.add(new_book)
        if is_admin() and new_book.status == 'available':
            notify_seller_followers_new_book(new_book)
            notify_wanted_match_for_book(new_book)
        db.session.commit()
        try:
            from services.rag_service import mark_index_stale
            mark_index_stale()  # 书籍变更后重建 RAG 索引
        except Exception:
            pass

        msg = '发布成功，等待管理员审核' if not is_admin() else '发布成功'
        return jsonify({
            'status': 'success', 
            'message': msg, 
            'book': new_book.to_dict(),
            'book_id': new_book.id
        })

    # 更新书籍信息
    @app.route('/api/books/<book_id>', methods=['PUT'])
    def update_book(book_id):
        """更新书籍；改价通知收藏用户；pending→available 触发审核通过通知"""
        if not is_logged_in():
            return jsonify({'status': 'error', 'message': '请先登录'}), 401
    
        data = request.json
        book = Book.query.filter_by(id=str(book_id)).first()
    
        if not book:
            return jsonify({'status': 'error', 'message': '书籍不存在'}), 404
    
        # 检查权限：只有书籍所有者或管理员可以更新
        user_id = str(session['user_id'])
        owner_id = str(book.owner_id or book.sellerId or '')
        if owner_id != user_id and not is_admin():
            return jsonify({'status': 'error', 'message': '无权限修改'}), 403
    
        # 验证必填字段
        if 'title' in data and (not data['title'] or not data['title'].strip()):
            return jsonify({'status': 'error', 'message': '书籍标题不能为空'}), 400
    
        if 'price' in data and (not data['price'] or float(data.get('price', 0)) <= 0):
            return jsonify({'status': 'error', 'message': '价格必须大于0'}), 400
    
        # 更新字段
        if 'title' in data:
            book.title = data['title'].strip()
        if 'author' in data:
            book.author = data.get('author', '').strip() or '未知作者'
        if 'category' in data:
            book.category = data['category']
        if 'condition' in data:
            book.condition = data['condition']
        if 'isbn' in data:
            book.isbn = data['isbn']
        for field in ('edition', 'course_code', 'campus_zone', 'dorm_building', 'campaign_tag', 'price_drop_until'):
            if field in data:
                setattr(book, field, (data[field] or '').strip())
        from services.campus_dorms import load_dorm_catalog, validate_dorm_zone
        _, by_zone, _ = load_dorm_catalog(Setting)
        ok, msg = validate_dorm_zone(book.dorm_building, book.campus_zone, by_zone)
        if not ok:
            return jsonify({'status': 'error', 'message': msg}), 400
        if 'original_price' in data:
            book.original_price = float(data['original_price']) if data['original_price'] not in (None, '') else None
        old_price = float(book.price) if book.price else 0
        old_status = book.status or ''
        if 'price' in data:
            book.price = float(data['price'])
        if 'desc' in data:
            book.desc = data['desc'].strip()
            book.description = data['desc'].strip()
        if 'description' in data:
            book.description = data['description'].strip()
            book.desc = data['description'].strip()
        if 'contact' in data:
            book.contact = data['contact'].strip()
        if 'imgs' in data:
            imgs = data['imgs']
            if isinstance(imgs, str):
                imgs = [imgs]
            try:
                imgs = normalize_book_images(flask_app, imgs, generate_id)
            except ValueError as e:
                return jsonify({'status': 'error', 'message': str(e)}), 400
            book.imgs = json.dumps(imgs, ensure_ascii=False)
            if imgs and len(imgs) > 0:
                book.image = imgs[0]
                book.cover_url = imgs[0]
        if 'stock' in data:
            book.stock = int(data.get('stock', 1))
        if 'status' in data:
            book.status = data['status']
    
        book.updated_at = time.strftime('%Y-%m-%d %H:%M:%S')
        if 'price' in data:
            notify_price_drop(book, old_price)
        if old_status != 'available' and book.status == 'available':
            push_notification(
                book.owner_id, 'audit',
                f'书籍审核通过：{book.title}',
                '您的书籍已上架',
                f'/book/{book.id}'
            )
            notify_seller_followers_new_book(book)
            notify_wanted_match_for_book(book)
        db.session.commit()
        try:
            from services.rag_service import mark_index_stale
            mark_index_stale()  # 书籍变更后重建 RAG 索引
        except Exception:
            pass

        d = book.to_dict()
        owner = User.query.filter_by(id=str(book.owner_id or '')).first()
        enrich_book_dict(d, owner)
        return jsonify({'status': 'success', 'message': '更新成功', 'book': d})

    # 删除书籍
    @app.route('/api/books/<book_id>', methods=['DELETE'])
    def delete_book(book_id):
        """删除书籍（已售不可删），级联删除收藏"""
        if not is_logged_in():
            return jsonify({'status': 'error', 'message': '请先登录'}), 401
    
        book = Book.query.filter_by(id=str(book_id)).first()
        if not book:
            return jsonify({'status': 'error', 'message': '书籍不存在'}), 404
    
        # 检查权限：只有书籍所有者或管理员可以删除
        if str(book.owner_id) != str(session['user_id']) and not is_admin():
            return jsonify({'status': 'error', 'message': '无权限删除'}), 403
    
        # 检查书籍是否已售出
        if book.status == 'sold':
            return jsonify({'status': 'error', 'message': '已售出的书籍不能删除'}), 400
    
        # 同时删除相关收藏
        Collection.query.filter_by(book_id=str(book_id)).delete()
    
        # 删除书籍
        db.session.delete(book)
        db.session.commit()
    
        return jsonify({'status': 'success', 'message': '删除成功'})


    @app.route('/api/books/<book_id>/clone', methods=['POST'])
    def clone_book(book_id):
        """复制已售书籍重新发布（待审核）"""
        if not is_logged_in():
            return jsonify({'status': 'error', 'message': '请先登录'}), 401
        src = Book.query.filter_by(id=str(book_id)).first()
        if not src:
            return jsonify({'status': 'error', 'message': '书籍不存在'}), 404
        if str(src.owner_id) != str(session['user_id']) and not is_admin():
            return jsonify({'status': 'error', 'message': '无权限'}), 403
        ts = time.strftime('%Y-%m-%d %H:%M:%S')
        status = 'available' if is_admin() else 'pending'
        new_book = Book(
            id=generate_id(),
            title=src.title,
            author=src.author,
            category=src.category,
            price=src.price,
            desc=src.desc,
            description=src.description or src.desc,
            imgs=src.imgs,
            image=src.image,
            cover_url=src.cover_url,
            contact=src.contact,
            stock=src.stock or 1,
            status=status,
            owner_id=str(session['user_id']),
            owner_name=session.get('username', ''),
            seller=session.get('username', ''),
            sellerId=str(session['user_id']),
            condition=src.condition,
            isbn=src.isbn,
            edition=src.edition,
            course_code=src.course_code,
            campus_zone=src.campus_zone,
            dorm_building=src.dorm_building,
            campaign_tag=src.campaign_tag,
            listing_type=src.listing_type or 'single',
            bundle_items=src.bundle_items,
            created_at=ts,
            createTime=ts,
            updated_at=ts
        )
        db.session.add(new_book)
        db.session.commit()
        msg = '已复制并提交审核' if status == 'pending' else '已复制上架'
        return jsonify({'status': 'success', 'message': msg, 'book': new_book.to_dict(), 'book_id': new_book.id})

