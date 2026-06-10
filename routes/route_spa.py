"""Vue SPA 页面路由与静态资源"""
import os

from flask import jsonify, redirect, request, send_from_directory, url_for


def register_spa_routes(app, helpers):
    """Flask 回退到 Vue dist；管理端页需 admin 校验；404 非 API 走 SPA"""
    dist_assets_dir = helpers['dist_assets_dir']
    serve_vue_or_503 = helpers['serve_vue_or_503']
    admin_vue_page = helpers['admin_vue_page']
    is_admin = helpers['is_admin']

    @app.route('/')
    def index():
        """首页 → index.html"""
        return serve_vue_or_503()

    @app.route('/feature/genuine')
    @app.route('/feature/low-price')
    @app.route('/feature/campus-trade')
    @app.route('/feature/new-condition')
    @app.route('/feature/exchange')
    def feature_pages():
        """营销落地页 /feature/*"""
        return serve_vue_or_503()

    @app.route('/admin/login')
    def admin_login_page():
        """已登录 admin 则跳转 /admin"""
        from flask import session
        if session.get('login_portal') == 'admin' and is_admin():
            return redirect('/admin')
        return serve_vue_or_503()

    @app.route('/admin')
    @app.route('/admin/analytics')
    @app.route('/admin/settings')
    @app.route('/admin/userManagement')
    @app.route('/admin/bookManagement')
    @app.route('/admin/orders')
    @app.route('/admin/campus')
    @app.route('/admin/wanted')
    @app.route('/admin/messages')
    @app.route('/admin/comments')
    @app.route('/admin/compliance')
    @app.route('/admin/books')
    @app.route('/admin/users')
    @app.route('/admin/sales')
    @app.route('/admin/pending')
    def admin_spa_pages():
        """管理后台各子路由统一入口"""
        return admin_vue_page()

    @app.route('/cart')
    @app.route('/transactionHistory')
    @app.route('/orderDetails')
    @app.route('/accountSettings')
    @app.route('/publishBook')
    @app.route('/booksList')
    @app.route('/personalCenter')
    @app.route('/myBooks')
    @app.route('/myCollections')
    @app.route('/guide')
    @app.route('/ai')
    @app.route('/courses')
    @app.route('/wanted')
    @app.route('/semester')
    @app.route('/messages')
    @app.route('/notifications')
    @app.route('/offers')
    @app.route('/campus/map')
    @app.route('/register')
    @app.route('/mySchedule')
    @app.route('/seller/<path:rest>')
    @app.route('/share/<path:rest>')
    @app.route('/feature/<path:rest>')
    def user_spa_pages():
        """前台 Vue history 路由统一 fallback"""
        return serve_vue_or_503()

    @app.route('/assets/<path:filename>')
    def vue_assets(filename):
        """Vite 构建产物 /assets/*"""
        target = os.path.join(dist_assets_dir, filename)
        if os.path.exists(target):
            return send_from_directory(dist_assets_dir, filename)
        return jsonify({'status': 'error', 'message': '资源不存在'}), 404

    @app.errorhandler(404)
    def page_not_found(e):
        """404：/api 返回 JSON；其余 history 路由 fallback SPA"""
        if request.path.startswith('/api/'):
            return jsonify({'status': 'error', 'message': 'API接口不存在'}), 404
        if request.path.startswith('/assets/'):
            return vue_assets(request.path.split('/assets/', 1)[-1])
        if request.path.startswith('/static/'):
            if request.path.endswith('.css'):
                if 'utils/variables.css' in request.path:
                    return redirect(url_for('static', filename='css/variables.css'))
                if 'utils/base.css' in request.path:
                    return redirect(url_for('static', filename='css/base.css'))
                if 'components/navbar.css' in request.path:
                    return redirect(url_for('static', filename='css/navbar.css'))
            return jsonify({'status': 'error', 'message': '静态文件不存在'}), 404
        return serve_vue_or_503()

    app.index = index
    app.vue_assets = vue_assets
