"""RAG 智能找书 API"""
from flask import jsonify, request

from models import Book, CourseTextbook, Announcement
from .rag_service import ask, ensure_index, rag_enabled, rebuild_index, status


def register_rag_routes(app, helpers):
    """AiAssistant 页：status / ask / 管理员 rebuild 索引"""
    is_admin = helpers['is_admin']

    @app.route('/api/ai/status', methods=['GET'])
    def ai_status():
        st = status()
        return jsonify({'status': 'success', **st})

    @app.route('/api/ai/ask', methods=['POST'])
    def ai_ask():
        """POST question → rag_service.ask"""
        if not rag_enabled():
            return jsonify({'status': 'error', 'message': '智能助手未开启'}), 503
        data = request.get_json(silent=True) or {}
        question = (data.get('question') or data.get('q') or '').strip()
        top_k = min(int(data.get('top_k', 5)), 10)
        result = ask(question, Book=Book, CourseTextbook=CourseTextbook, Announcement=Announcement, top_k=top_k)
        return jsonify({'status': 'success', **result})

    @app.route('/api/ai/rebuild', methods=['POST'])
    def ai_rebuild():
        if not is_admin():
            return jsonify({'status': 'error', 'message': '需要管理员权限'}), 403
        data = request.get_json(silent=True) or {}
        with_emb = bool(data.get('with_embeddings'))
        n = rebuild_index(Book, CourseTextbook, Announcement, with_embeddings=with_emb)
        return jsonify({'status': 'success', 'message': f'索引已重建，共 {n} 条', 'indexed_count': n})

    @app.route('/api/ai/ensure-index', methods=['POST'])
    def ai_ensure_index():
        if not is_admin():
            return jsonify({'status': 'error', 'message': '需要管理员权限'}), 403
        n = ensure_index(Book, CourseTextbook, Announcement)
        return jsonify({'status': 'success', 'indexed_count': n})
