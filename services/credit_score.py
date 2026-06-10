"""用户综合信用分"""
from models import db, User, Order, Review, Report


def compute_user_credit(user):
    """100 分制：爽约/举报扣分，交易/评价/认证加分"""
    if not user:
        return None
    uid = str(user.id)
    score = 100
    factors = []

    no_show = int(user.no_show_count or 0)
    if no_show:
        d = min(no_show * 8, 40)
        score -= d
        factors.append({'label': f'面交爽约 {no_show} 次', 'delta': -d})

    reports = Report.query.filter_by(
        target_type='user', target_id=uid, status='handled'
    ).count()
    if reports:
        d = min(reports * 12, 36)
        score -= d
        factors.append({'label': f'违规举报成立 {reports} 次', 'delta': -d})

    if (user.ban_level or 'none') == 'warning':
        score -= 5
        factors.append({'label': '警告记录', 'delta': -5})

    sell_done = Order.query.filter_by(seller_id=uid, status='completed').count()
    buy_done = Order.query.filter_by(buyer_id=uid, status='completed').count()
    trade_bonus = min((sell_done + buy_done) * 2, 24)
    if trade_bonus:
        score += trade_bonus
        factors.append({'label': f'完成交易 {sell_done + buy_done} 笔', 'delta': trade_bonus})

    reviews = Review.query.filter_by(reviewed_user_id=uid).all()
    if reviews:
        avg = sum(
            (r.description_rating or r.service_rating or 0) + (r.service_rating or 0) +
            (r.condition_rating or 0) + (r.efficiency_rating or 0)
            for r in reviews
        ) / (len(reviews) * 4)
        rating_bonus = int(max(0, (avg - 3.5) * 8))
        rating_bonus = min(rating_bonus, 10)
        if rating_bonus:
            score += rating_bonus
            factors.append({'label': f'评价均分 {avg:.1f}', 'delta': rating_bonus})

    if user.campus_verified:
        score += 5
        factors.append({'label': '校园认证', 'delta': 5})

    score = max(0, min(100, int(round(score))))
    if score >= 90:
        level, tag = '优秀', '信用优秀'
    elif score >= 75:
        level, tag = '良好', '信用良好'
    elif score >= 60:
        level, tag = '一般', '信用一般'
    else:
        level, tag = '待提升', '信用待提升'

    return {
        'score': score,
        'level': level,
        'credit_tag': tag,
        'factors': factors,
        'no_show_count': no_show,
        'completed_trades': sell_done + buy_done,
        'handled_reports': reports,
        'review_count': len(reviews),
        'restrict_appointment': no_show >= 3
    }


def register_credit_routes(app, helpers):
    """GET /api/my/credit、/api/users/:id/credit"""
    from flask import jsonify, session

    is_logged_in = helpers['is_logged_in']

    @app.route('/api/users/<user_id>/credit', methods=['GET'])
    def user_credit(user_id):
        """公开查询指定用户信用分"""
        u = User.query.filter_by(id=str(user_id)).first()
        if not u:
            return jsonify({'status': 'error', 'message': '用户不存在'}), 404
        return jsonify({'status': 'success', 'credit': compute_user_credit(u)})

    @app.route('/api/my/credit', methods=['GET'])
    def my_credit():
        """当前登录用户信用分"""
        if not is_logged_in():
            return jsonify({'status': 'error', 'message': '请先登录'}), 401
        u = User.query.filter_by(id=str(session['user_id'])).first()
        return jsonify({'status': 'success', 'credit': compute_user_credit(u)})
