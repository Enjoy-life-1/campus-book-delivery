"""ISBN/校园/学期/书籍扩展 API"""
import json
import os
import re
import time
import urllib.parse
import urllib.request

from flask import jsonify, request, session

from services.campus_features import refresh_semester_campaigns, enrich_campaign_dict
from models import db, User, Book, Setting, CampusSpot, CourseTextbook, SemesterCampaign


def register_catalog_routes(app, helpers):
    """注册 ISBN 查询、校园/课程/学期、降价、相似书 API"""
    generate_id = helpers['generate_id']
    is_logged_in = helpers['is_logged_in']
    is_admin = helpers['is_admin']
    enrich_book_dict = helpers['enrich_book_dict']
    find_similar_books = helpers['find_similar_books']
    notify_price_drop = helpers['notify_price_drop']
    push_notification = helpers['push_notification']
    app_ref = helpers.get('app') or app


    def _fetch_isbn_json(url, headers=None, timeout=10):
        req = urllib.request.Request(url, headers=headers or {'User-Agent': 'CampusBookDelivery/1.0'})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode('utf-8'))


    def _isbn_book_dict(clean, title, author='', cover='', edition='', desc='', source=''):
        return {
            'title': (title or '').strip(),
            'author': (author or '').strip() or '未知作者',
            'isbn': clean,
            'cover_url': (cover or '').strip(),
            'edition': (edition or '').strip(),
            'desc': (desc or '').strip(),
            'source': source,
        }


    def _lookup_isbn_juhe(clean, key):
        url = (
            'http://apis.juhe.cn/isbn/query?'
            + urllib.parse.urlencode({'isbn': clean, 'key': key})
        )
        data = _fetch_isbn_json(url)
        if data.get('error_code') != 0:
            return None
        info = (data.get('result') or {}).get('data') or data.get('result') or {}
        title = (info.get('title') or '').strip()
        if not title:
            return None
        cover = (info.get('img') or info.get('images_large') or info.get('smallImg') or '').strip()
        pub = (info.get('pubDate') or info.get('pubdate') or '').strip()
        publisher = (info.get('publisher') or '').strip()
        edition = ' '.join(x for x in (publisher, pub) if x)
        return _isbn_book_dict(
            clean, title, info.get('author') or '', cover, edition,
            info.get('gist') or info.get('summary') or '', 'juhe'
        )


    def _lookup_isbn_bamboo_legacy(clean):
        data = _fetch_isbn_json(f'https://isbn.qiaohaoforever.cn/{clean}')
        title = (data.get('title') or '').strip()
        if not title:
            return None
        return _isbn_book_dict(
            clean, title, data.get('author') or '', data.get('image') or '',
            data.get('publisher') or '', data.get('summary') or '', 'bamboo'
        )


    def _lookup_isbn_feelyou(clean, apikey):
        url = f'https://api.feelyou.top/isbn/{clean}'
        data = _fetch_isbn_json(url, headers={'apikey': apikey, 'User-Agent': 'CampusBookDelivery/1.0'})
        title = (data.get('title') or '').strip()
        if not title:
            return None
        bi = data.get('book_info') or {}
        author = bi.get('作者') or bi.get('author') or ''
        publisher = bi.get('出版社') or ''
        pub_year = bi.get('出版年') or ''
        edition = ' '.join(x for x in (publisher, pub_year) if x)
        return _isbn_book_dict(
            clean, title, author, data.get('cover_url') or '',
            edition, data.get('book_intro') or data.get('abstract') or '', 'feelyou'
        )


    def _lookup_isbn_domestic(clean):
        """多源 ISBN 查询：聚合数据 → feelyou → bamboo 备用"""
        settings = Setting.get_all_as_dict()
        juhe_key = (settings.get('juhe_isbn_key') or os.environ.get('JUHE_ISBN_KEY', '')).strip()
        bamboo_key = (settings.get('bamboo_isbn_apikey') or os.environ.get('BAMBOO_ISBN_APIKEY', '')).strip()
        providers = []
        if juhe_key:
            providers.append(lambda: _lookup_isbn_juhe(clean, juhe_key))
        if bamboo_key:
            providers.append(lambda: _lookup_isbn_feelyou(clean, bamboo_key))
        providers.extend([
            lambda: _lookup_isbn_bamboo_legacy(clean),
        ])
        last_err = None
        for fn in providers:
            try:
                book = fn()
                if book and book.get('title'):
                    return book, None
            except Exception as e:
                last_err = e
        return None, last_err


    @app.route('/api/isbn/<isbn>', methods=['GET'])
    def lookup_isbn(isbn):
        """扫码/手输 ISBN → 书名作者封面（发布页用）"""
        clean = re.sub(r'[^0-9Xx]', '', isbn or '')
        if len(clean) < 10:
            return jsonify({'status': 'error', 'message': 'ISBN格式不正确'}), 400
        book, err = _lookup_isbn_domestic(clean)
        if not book:
            msg = '未找到该ISBN，请手动填写'
            if err:
                msg = f'ISBN查询失败: {err}'
            return jsonify({'status': 'error', 'message': msg}), 404
        return jsonify({'status': 'success', 'book': book})


    @app.route('/api/campus/spots', methods=['GET'])
    def campus_spots():
        """面交点列表（含地图坐标）"""
        rows = CampusSpot.query.order_by(CampusSpot.sort_order).all()
        return jsonify({'status': 'success', 'spots': [s.to_dict() for s in rows]})


    @app.route('/api/campus/dorms', methods=['GET'])
    def campus_dorms():
        """按校区返回可选楼栋"""
        from services.campus_dorms import load_dorm_catalog, dorms_for_zone
        zone = (request.args.get('campus_zone') or '').strip()
        items, by_zone, all_names = load_dorm_catalog(Setting)
        dorms = dorms_for_zone(by_zone, zone) if zone else all_names
        return jsonify({
            'status': 'success',
            'dorms': dorms,
            'by_zone': by_zone,
            'items': items,
        })


    @app.route('/api/courses', methods=['GET'])
    def list_courses():
        """课表教材目录，可按学院/专业筛选"""
        college = (request.args.get('college') or '').strip()
        major = (request.args.get('major') or '').strip()
        q = CourseTextbook.query
        if college:
            q = q.filter_by(college=college)
        if major:
            q = q.filter_by(major=major)
        rows = q.order_by(CourseTextbook.college, CourseTextbook.major).all()
        colleges = sorted({r.college for r in rows})
        majors = sorted({r.major for r in rows})
        return jsonify({
            'status': 'success',
            'courses': [r.to_dict() for r in rows],
            'colleges': colleges,
            'majors': majors
        })


    @app.route('/api/courses/<course_code>/books', methods=['GET'])
    def course_books(course_code):
        """按课程代码匹配在售教材（course_code / 书名 / ISBN）"""
        ct = CourseTextbook.query.filter_by(course_code=course_code).first()
        books = Book.query.filter_by(status='available').all()
        result = []
        code = course_code.strip()
        kw = (ct.textbook_title if ct else '').lower()
        isbn = (ct.textbook_isbn if ct else '').strip()
        for book in books:
            hit = (book.course_code or '') == code
            if not hit and kw and kw in (book.title or '').lower():
                hit = True
            if not hit and isbn and isbn in (book.isbn or ''):
                hit = True
            if hit:
                d = book.to_dict()
                owner = User.query.filter_by(id=str(book.owner_id or '')).first()
                enrich_book_dict(d, owner)
                result.append(d)
        return jsonify({
            'status': 'success',
            'course': ct.to_dict() if ct else None,
            'books': result
        })


    @app.route('/api/semester/active', methods=['GET'])
    def semester_active():
        """当前学期专场活动及关联书籍"""
        refresh_semester_campaigns()
        campaigns = SemesterCampaign.query.filter_by(is_active=True).all()
        if not campaigns:
            campaigns = SemesterCampaign.query.all()[:1]
        tags = [c.tag for c in campaigns if c.tag]
        books = []
        if tags:
            for book in Book.query.filter_by(status='available').all():
                if (book.campaign_tag or '') in tags:
                    d = book.to_dict()
                    owner = User.query.filter_by(id=str(book.owner_id or '')).first()
                    enrich_book_dict(d, owner)
                    books.append(d)
        return jsonify({
            'status': 'success',
            'campaigns': [enrich_campaign_dict(c) for c in campaigns],
            'books': books[:24]
        })


    @app.route('/api/books/<book_id>/price-drop', methods=['POST'])
    def set_price_drop(book_id):
        """卖家设置倒计时或阶梯降价；notify_price_drop 通知收藏用户"""
        if not is_logged_in():
            return jsonify({'status': 'error', 'message': '请先登录'}), 401
        book = Book.query.filter_by(id=str(book_id)).first()
        if not book:
            return jsonify({'status': 'error', 'message': '书籍不存在'}), 404
        if str(book.owner_id) != str(session['user_id']) and not is_admin():
            return jsonify({'status': 'error', 'message': '无权限'}), 403
        data = request.json or {}
        mode = (data.get('mode') or 'countdown').strip()
        if mode == 'ladder':
            steps = data.get('steps') or []
            if not steps:
                return jsonify({'status': 'error', 'message': '请提供阶梯降价步骤'}), 400
            if not book.original_price:
                book.original_price = float(book.price)
            book.price_drop_plan = json.dumps({
                'mode': 'ladder',
                'started_at': time.strftime('%Y-%m-%d %H:%M:%S'),
                'steps': steps
            }, ensure_ascii=False)
            first = min(steps, key=lambda x: float(x.get('hours', 0)))
            fp = float(first.get('price', 0))
            if fp > 0 and fp < float(book.price):
                old = float(book.price)
                book.price = fp
                notify_price_drop(book, old)
            last_h = max(float(s.get('hours', 72)) for s in steps)
            book.price_drop_until = (datetime.now() + timedelta(hours=last_h)).strftime('%Y-%m-%d %H:%M:%S')
            msg = '阶梯自动降价已开启'
        else:
            hours = int(data.get('hours', 72))
            target = float(data.get('target_price', book.price))
            if target <= 0 or target >= float(book.price):
                return jsonify({'status': 'error', 'message': '目标价须低于当前价'}), 400
            if not book.original_price:
                book.original_price = float(book.price)
            old = float(book.price)
            book.price = target
            book.price_drop_plan = None
            book.price_drop_until = (datetime.now() + timedelta(hours=hours)).strftime('%Y-%m-%d %H:%M:%S')
            notify_price_drop(book, old)
            msg = '倒计时降价已开启'
        book.updated_at = time.strftime('%Y-%m-%d %H:%M:%S')
        db.session.commit()
        d = book.to_dict()
        enrich_book_dict(d)
        return jsonify({'status': 'success', 'message': msg, 'book': d})


    @app.route('/api/books/<book_id>/similar', methods=['GET'])
    def similar_books(book_id):
        """相似书籍推荐"""
        book = Book.query.filter_by(id=str(book_id)).first()
        if not book:
            return jsonify({'status': 'error', 'message': '书籍不存在'}), 404
        return jsonify({'status': 'success', 'books': find_similar_books(book)})



