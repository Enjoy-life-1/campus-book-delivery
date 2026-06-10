"""RAG 服务测试：索引重建与问答"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_rag_status_and_ask():
    """RAG 索引重建 + 问答返回 answer/sources"""
    os.environ.setdefault('RAG_ENABLED', '1')
    from app import app
    from models import Book, CourseTextbook, Announcement
    from services.rag_service import rebuild_index, ask, status

    with app.app_context():
        rebuild_index(Book, CourseTextbook, Announcement, with_embeddings=False)
        st = status()
        assert st.get('enabled') is True
        assert st.get('indexed_count', 0) > 0
        out = ask('如何学籍认证', Book=Book, CourseTextbook=CourseTextbook, Announcement=Announcement)
        assert out.get('answer')
        assert isinstance(out.get('sources'), list)
