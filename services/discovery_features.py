"""发现与智能：搜索联想、浏览推荐、历史成交价、课程版次提示"""
import re
from collections import Counter

from flask import jsonify, request, session
from sqlalchemy import func

from models import db, Book, Order, CourseTextbook, BookView, User


def _tokens(keyword):
    """搜索词分词"""
    kw = (keyword or '').strip().lower()
    if not kw:
        return []
    return [t for t in re.split(r'[\s,，、]+', kw) if len(t) >= 1]


def build_search_filter(keyword):
    """多词 AND 匹配，比单条 contains 更准"""
    parts = _tokens(keyword)
    if not parts:
        return None
    flt = None
    for t in parts:
        piece = db.or_(
            func.lower(Book.title).contains(t),
            func.lower(Book.author).contains(t),
            func.lower(Book.isbn).contains(t),
            func.lower(Book.owner_name).contains(t),
            func.lower(Book.seller).contains(t),
            func.lower(Book.course_code).contains(t),
            func.lower(Book.desc).contains(t),
        )
        flt = piece if flt is None else db.and_(flt, piece)
    return flt


def search_suggestions(keyword, limit=10):
    """BooksList 搜索框 datalist 联想"""
    parts = _tokens(keyword)
    if not parts:
        return []
    q = Book.query.filter_by(status='available')
    sf = build_search_filter(keyword)
    if sf is not None:
        q = q.filter(sf)
    rows = q.limit(80).all()
    seen = set()
    out = []
    for b in rows:
        for label in (b.title, b.author, b.isbn):
            if not label:
                continue
            key = label.lower()
            if key in seen:
                continue
            if all(p in key for p in parts):
                seen.add(key)
                out.append({'type': 'title' if label == b.title else ('isbn' if label == b.isbn else 'author'), 'text': label, 'book_id': b.id})
                if len(out) >= limit:
                    return out
    return out


def price_insights(book):
    """同类历史成交价与在售比价"""
    isbn = (book.isbn or '').strip()
    cat = book.category or ''
    course = (book.course_code or '').strip()
    prices = []
    q = Order.query.filter_by(status='completed', order_type='sale')
    if isbn:
        bids = [b.id for b in Book.query.filter_by(isbn=isbn).all()]
        if bids:
            for o in q.filter(Order.book_id.in_(bids)).all():
                if o.price:
                    prices.append(float(o.price))
    if len(prices) < 3 and course:
        bids = [b.id for b in Book.query.filter_by(course_code=course).all()]
        if bids:
            for o in q.filter(Order.book_id.in_(bids)).all():
                if o.price:
                    prices.append(float(o.price))
    if len(prices) < 3 and cat:
        bids = [b.id for b in Book.query.filter_by(category=cat).all()]
        if bids:
            for o in q.filter(Order.book_id.in_(bids)).limit(50).all():
                if o.price:
                    prices.append(float(o.price))
    on_sale = []
    sq = Book.query.filter_by(status='available')
    if isbn:
        on_sale = [float(b.price) for b in sq.filter_by(isbn=isbn).all() if b.price]
    elif course:
        on_sale = [float(b.price) for b in sq.filter_by(course_code=course).all() if b.price]
    elif cat:
        on_sale = [float(b.price) for b in sq.filter_by(category=cat).limit(30).all() if b.price]
    if not prices and not on_sale:
        return None
    all_p = prices + on_sale
    avg = round(sum(all_p) / len(all_p), 2) if all_p else None
    hist_avg = round(sum(prices) / len(prices), 2) if prices else None
    cur = float(book.price or 0)
    hint = ''
    if avg and cur:
        if cur > avg * 1.15:
            hint = '高于同类均价，可适当降价'
        elif cur < avg * 0.85:
            hint = '低于同类均价，性价比较高'
        else:
            hint = '价格接近同类均价'
    return {
        'sample_count': len(all_p),
        'history_count': len(prices),
        'avg_price': avg,
        'history_avg_price': hist_avg,
        'min_price': round(min(all_p), 2) if all_p else None,
        'max_price': round(max(all_p), 2) if all_p else None,
        'on_sale_count': len(on_sale),
        'current_price': cur,
        'hint': hint
    }


def publish_hints(data):
    """版次/课程适配提示"""
    warnings = []
    tips = []
    isbn = (data.get('isbn') or '').strip()
    course_code = (data.get('course_code') or '').strip()
    edition = (data.get('edition') or '').strip()
    title = (data.get('title') or '').strip()
    if course_code:
        ct = CourseTextbook.query.filter_by(course_code=course_code).first()
        if ct:
            tips.append(f'课程 {course_code} 推荐教材：《{ct.textbook_title}》')
            if ct.textbook_isbn and isbn and ct.textbook_isbn != isbn:
                warnings.append(f'ISBN 与课程推荐教材不一致（推荐 {ct.textbook_isbn}）')
            if ct.textbook_title and title and ct.textbook_title[:4] not in title:
                warnings.append('书名与课程推荐教材名称差异较大，请核对是否选错课程')
        else:
            warnings.append('课程代码未在课表库中，买家可能难以按课检索')
    if isbn and not edition:
        warnings.append('建议填写版次/出版年，便于买家确认教材版本')
    if edition and not re.search(r'\d', edition):
        tips.append('版次建议包含版号或年份，如「第7版」或「2022」')
    price = data.get('price')
    if isbn and price not in (None, ''):
        fake = Book(isbn=isbn, category=data.get('category') or 'textbook', course_code=course_code, price=float(price))
        ins = price_insights(fake)
        if ins and ins.get('hint'):
            tips.append(ins['hint'])
    return {'warnings': warnings, 'tips': tips}


def personalized_books(user_id, exclude_book_id=None, limit=8):
    """根据 BookView 浏览史推荐同类/同课书籍"""
    uid = str(user_id or '')
    if not uid:
        return []
    views = BookView.query.filter_by(user_id=uid).order_by(BookView.created_at.desc()).limit(30).all()
    if not views:
        return []
    book_ids = [v.book_id for v in views]
    viewed = Book.query.filter(Book.id.in_(book_ids)).all()
    cats = Counter(b.category for b in viewed if b.category)
    courses = Counter(b.course_code for b in viewed if b.course_code)
    isbns = {b.isbn for b in viewed if b.isbn}
    candidates = Book.query.filter_by(status='available').all()
    scored = []
    for b in candidates:
        if exclude_book_id and str(b.id) == str(exclude_book_id):
            continue
        if str(b.owner_id) == uid:
            continue
        score = 0
        if b.isbn and b.isbn in isbns:
            score += 8
        if b.category and cats.get(b.category):
            score += cats[b.category] * 2
        if b.course_code and courses.get(b.course_code):
            score += courses[b.course_code] * 3
        if score > 0:
            scored.append((score, b))
    scored.sort(key=lambda x: -x[0])
    return [b.to_dict() for _, b in scored[:limit]]


def merge_recommendations(find_similar_fn, book, user_id=None, limit=6):
    """相似书 + 个性化浏览推荐合并去重"""
    base = find_similar_fn(book, limit=limit)
    if not user_id:
        return base
    personal = personalized_books(user_id, exclude_book_id=book.id, limit=limit)
    seen = {b['id'] for b in base}
    for p in personal:
        if p['id'] not in seen:
            base.append(p)
            seen.add(p['id'])
        if len(base) >= limit:
            break
    return base[:limit]


def register_discovery_routes(app, helpers):
    """搜索联想、比价、个性化推荐、发布提示 API"""
    is_logged_in = helpers['is_logged_in']

    @app.route('/api/search/suggest', methods=['GET'])
    def search_suggest():
        """GET /api/search/suggest?q="""
        q = (request.args.get('q') or request.args.get('search') or '').strip()
        if len(q) < 1:
            return jsonify({'status': 'success', 'suggestions': []})
        return jsonify({
            'status': 'success',
            'suggestions': search_suggestions(q, int(request.args.get('limit', 10)))
        })

    @app.route('/api/books/<book_id>/price-insights', methods=['GET'])
    def book_price_insights(book_id):
        """书籍详情页同类比价"""
        book = Book.query.filter_by(id=str(book_id)).first()
        if not book:
            return jsonify({'status': 'error', 'message': '书籍不存在'}), 404
        ins = price_insights(book)
        return jsonify({'status': 'success', 'insights': ins})

    @app.route('/api/recommendations/for-you', methods=['GET'])
    def recommendations_for_you():
        """首页/详情「猜你喜欢」"""
        if not is_logged_in():
            return jsonify({'status': 'success', 'books': []})
        books = personalized_books(session['user_id'], limit=int(request.args.get('limit', 12)))
        enrich = helpers.get('enrich_book_dict')
        owners = {}
        if enrich and books:
            oids = {b.get('owner_id') for b in books if b.get('owner_id')}
            for u in User.query.filter(User.id.in_(list(oids))).all():
                owners[str(u.id)] = u
            for b in books:
                enrich(b, owners.get(str(b.get('owner_id'))))
        return jsonify({'status': 'success', 'books': books})

    @app.route('/api/publish/hints', methods=['GET'])
    def publish_hints_api():
        """发布页版次/课程/价格提示"""
        data = {
            'isbn': request.args.get('isbn', ''),
            'course_code': request.args.get('course_code', ''),
            'edition': request.args.get('edition', ''),
            'title': request.args.get('title', ''),
            'price': request.args.get('price', ''),
            'category': request.args.get('category', 'textbook'),
        }
        h = publish_hints(data)
        return jsonify({'status': 'success', **h})
