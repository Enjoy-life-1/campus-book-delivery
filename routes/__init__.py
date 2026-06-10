"""统一注册全部路由与扩展模块"""
from .route_admin import register_admin_routes  # 管理后台核心 API
from .route_admin_ext import register_admin_ext_routes  # 分类/公告/校园 CRUD
from .route_auth import register_auth_routes  # 登录注册
from .route_books import register_books_routes  # 书籍
from .route_cart import register_cart_routes  # 购物车
from .route_catalog import register_catalog_routes  # ISBN/课程/学期
from .route_community import register_community_routes  # 收藏/评论/求购
from .route_messaging import register_messaging_routes  # 私信/通知
from .route_orders import register_orders_routes  # 订单
from .route_spa import register_spa_routes  # Vue 页面回退

from services.admin_compliance import register_compliance_routes  # 举报/封禁
from services.book_media import register_book_media  # 图片上传
from services.campus_features import register_campus_features  # 课表/宿舍地图
from services.credit_score import register_credit_routes  # 信用分
from services.discovery_features import register_discovery_routes  # 搜索推荐
from services.messaging import register_chat_sock  # WebSocket
from services.priority_features import register_priority_routes
from services.rag_features import register_rag_routes  # RAG AI
from services.seller_tools import register_seller_tools  # 卖家工具

from app_helpers import (
    admin_vue_page, enrich_book_dict, find_wanted_matches,
    generate_id, is_admin, is_full_admin, is_logged_in, notify_price_drop,
    seller_profile_stats, serve_vue_or_503,
)


def register_all_routes(app, helpers, auth_exports):
    """挂载所有 HTTP 路由与扩展，返回 auth 处理器字典"""
    h = helpers
    register_books_routes(app, h)
    register_orders_routes(app, h)
    register_community_routes(app, h)
    register_messaging_routes(app, h)
    register_catalog_routes(app, h)
    register_admin_routes(app, h)
    register_cart_routes(app, h)
    register_admin_ext_routes(app, h)

    register_spa_routes(app, {  # 非 API 的 Vue 页面路由
        'dist_assets_dir': auth_exports['dist_assets_dir'],
        'serve_vue_or_503': serve_vue_or_503,
        'admin_vue_page': admin_vue_page,
        'is_admin': is_admin,
    })

    register_priority_routes(app)  # 学校/认证/举报/换书等
    register_chat_sock(app)  # WebSocket /ws/chat
    register_compliance_routes(app, {
        'is_logged_in': is_logged_in,
        'is_admin': is_admin,
        'is_full_admin': is_full_admin,
    })
    register_seller_tools(app, {
        'is_logged_in': is_logged_in,
        'generate_id': generate_id,
        'enrich_book_dict': enrich_book_dict,
        'notify_price_drop': notify_price_drop,
        'find_wanted_matches': find_wanted_matches,
        'seller_profile_stats': seller_profile_stats,
    })
    register_campus_features(app, {
        'is_logged_in': is_logged_in,
        'generate_id': generate_id,
        'is_admin': is_admin,
    })
    register_discovery_routes(app, {
        'is_logged_in': is_logged_in,
        'enrich_book_dict': enrich_book_dict,
    })
    register_book_media(app, generate_id)
    register_credit_routes(app, {'is_logged_in': is_logged_in})
    register_rag_routes(app, {'is_admin': is_admin})

    return register_auth_routes(app, {  # 最后注册 auth
        'generate_id': generate_id,
        'is_logged_in': is_logged_in,
        'is_admin': is_admin,
        'is_staff_user': auth_exports['is_staff_user'],
        'gateway_url': auth_exports['gateway_url'],
        'send_channel_message': auth_exports['send_channel_message'],
        'serve_vue_or_503': serve_vue_or_503,
    })
