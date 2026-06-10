"""轻量 RAG：书籍/课程/公告/指南检索 + 可选 OpenAI 兼容 LLM 生成"""
import json
import math
import os
import re
import time
import urllib.error
import urllib.request
from pathlib import Path

RAG_DIR = Path(__file__).resolve().parent / 'data' / 'rag'
CHUNKS_FILE = RAG_DIR / 'chunks.json'
META_FILE = RAG_DIR / 'meta.json'

HELP_CHUNKS = [
    {
        'id': 'help_trade',
        'type': 'guide',
        'title': '交易指南',
        'text': '校园书递支持二手教材转让：浏览书籍、收藏、购物车下单、私信议价、预约校内面交点完成交易。请在本校认证后发布与购买。',
        'link': '/guide',
    },
    {
        'id': 'help_verify',
        'type': 'guide',
        'title': '学籍认证',
        'text': '在个人中心完成学籍认证，使用学校邮箱（如 @stu.baiyunu.edu.cn）验证后可发布书籍、参与求购与学期专场活动。',
        'link': '/personalCenter',
    },
    {
        'id': 'help_campus',
        'type': 'guide',
        'title': '校区与面交',
        'text': '请选择西校区或北校区及对应宿舍楼栋；面交可在图书馆、食堂、教学楼等校园面交点进行，详见宿舍地图与书籍详情中的校区信息。',
        'link': '/campus/map',
    },
    {
        'id': 'help_course',
        'type': 'guide',
        'title': '按课找书',
        'text': '在「按课找书」页面按学院、专业、课程代码查找教材映射，并跳转到在售二手书列表。',
        'link': '/courses',
    },
]


def rag_enabled():
    return os.environ.get('RAG_ENABLED', '1').lower() in ('1', 'true', 'yes')


def _api_key():
    return (os.environ.get('LLM_API_KEY') or os.environ.get('DASHSCOPE_API_KEY') or '').strip()


def _dashscope_active():
    return bool((os.environ.get('DASHSCOPE_API_KEY') or '').strip())


def llm_configured():
    return bool(_api_key())


def _base_url():
    url = (os.environ.get('LLM_BASE_URL') or '').strip()
    if url:
        return url.rstrip('/')
    if _dashscope_active():
        return 'https://dashscope.aliyuncs.com/compatible-mode/v1'
    return 'https://api.openai.com/v1'


def _embed_model():
    if (os.environ.get('EMBEDDING_MODEL') or '').strip():
        return os.environ.get('EMBEDDING_MODEL').strip()
    if _dashscope_active():
        return 'text-embedding-v3'
    return 'text-embedding-3-small'


def _chat_model():
    if (os.environ.get('LLM_MODEL') or '').strip():
        return os.environ.get('LLM_MODEL').strip()
    if _dashscope_active():
        return 'qwen-plus'
    return 'gpt-4o-mini'


def _llm_provider():
    if not llm_configured():
        return 'none'
    if _dashscope_active() and not (os.environ.get('LLM_API_KEY') or '').strip():
        return 'dashscope'
    if 'dashscope' in _base_url():
        return 'dashscope'
    return 'openai'


def _tokenize(text):
    text = (text or '').lower()
    parts = re.findall(r'[\u4e00-\u9fff]|[a-z0-9]{2,}', text)
    if not parts:
        return set()
    bigrams = set(parts)
    for i in range(len(parts) - 1):
        if '\u4e00' <= parts[i][0] <= '\u9fff' and '\u4e00' <= parts[i + 1][0] <= '\u9fff':
            bigrams.add(parts[i] + parts[i + 1])
    return bigrams


def _lexical_score(query, doc):
    q = _tokenize(query)
    d = _tokenize(doc)
    if not q or not d:
        return 0.0
    hit = len(q & d)
    return hit / (len(q) ** 0.5)


def _cosine(a, b):
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def _api_post(path, payload):
    key = _api_key()
    if not key:
        return None
    body = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(
        f'{_base_url()}{path}',
        data=body,
        headers={'Content-Type': 'application/json', 'Authorization': f'Bearer {key}'},
        method='POST',
    )
    with urllib.request.urlopen(req, timeout=45) as resp:
        return json.loads(resp.read().decode('utf-8'))


def embed_text(text):
    try:
        data = _api_post('/embeddings', {'model': _embed_model(), 'input': text[:2000]})
        if data and data.get('data'):
            return data['data'][0]['embedding']
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, KeyError, OSError):
        pass
    return None


def _load_chunks():
    if not CHUNKS_FILE.is_file():
        return []
    try:
        with open(CHUNKS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return []


def _save_chunks(chunks, meta=None):
    RAG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CHUNKS_FILE, 'w', encoding='utf-8') as f:
        json.dump(chunks, f, ensure_ascii=False)
    m = meta or {}
    m['updated_at'] = time.strftime('%Y-%m-%d %H:%M:%S')
    m['count'] = len(chunks)
    with open(META_FILE, 'w', encoding='utf-8') as f:
        json.dump(m, f, ensure_ascii=False)


def build_chunks_from_db(Book, CourseTextbook, Announcement, limit_books=500):
    """从 DB 抽取书籍/课程/公告 + 内置 HELP_CHUNKS 写入 chunks.json"""
    chunks = list(HELP_CHUNKS)
    for b in Book.query.filter_by(status='available').order_by(Book.created_at.desc()).limit(limit_books).all():
        text = ' '.join(filter(None, [
            b.title, b.author, b.desc or b.description,
            b.course_code, b.isbn, b.campus_zone, b.dorm_building, b.condition,
        ]))
        if not text.strip():
            continue
        chunks.append({
            'id': f'book_{b.id}',
            'type': 'book',
            'title': b.title,
            'text': f'在售二手书《{b.title}》作者{b.author or "未知"}，价格¥{b.price}，'
                    f'校区{b.campus_zone or ""} {b.dorm_building or ""}，'
                    f'课程{b.course_code or "-"} ISBN {b.isbn or "-"}。{b.desc or b.description or ""}',
            'link': f'/book/{b.id}',
            'book_id': b.id,
        })
    for c in CourseTextbook.query.limit(300).all():
        chunks.append({
            'id': f'course_{c.id}',
            'type': 'course',
            'title': c.course_name or c.course_code,
            'text': f'{c.college} {c.major} 课程{c.course_code} {c.course_name} '
                    f'教材《{c.textbook_title}》{c.textbook_author} ISBN {c.textbook_isbn}',
            'link': f'/courses?code={c.course_code}',
        })
    for a in Announcement.query.filter_by(is_active=True).limit(20).all():
        chunks.append({
            'id': f'ann_{a.id}',
            'type': 'announcement',
            'title': a.title,
            'text': f'{a.title}。{a.content}',
            'link': '/',
        })
    return chunks


def rebuild_index(Book, CourseTextbook, Announcement, with_embeddings=False):
    """重建检索索引；可选调用 embedding API"""
    chunks = build_chunks_from_db(Book, CourseTextbook, Announcement)
    if with_embeddings and llm_configured():
        for ch in chunks:
            ch['embedding'] = embed_text(ch['text'][:1500])
    else:
        for ch in chunks:
            ch.pop('embedding', None)
    _save_chunks(chunks, {'with_embeddings': with_embeddings and llm_configured()})
    return len(chunks)


def mark_index_stale():
    """书籍/课程变更后标记索引失效，下次问答时自动重建"""
    for path in (CHUNKS_FILE, META_FILE):
        try:
            if path.is_file():
                path.unlink()
        except OSError:
            pass


def ensure_index(Book, CourseTextbook, Announcement):
    if not rag_enabled():
        return 0
    if CHUNKS_FILE.is_file():
        return len(_load_chunks())
    return rebuild_index(Book, CourseTextbook, Announcement, with_embeddings=False)


def status():
    meta = {}
    if META_FILE.is_file():
        try:
            with open(META_FILE, 'r', encoding='utf-8') as f:
                meta = json.load(f)
        except (json.JSONDecodeError, OSError):
            meta = {}
    chunks = _load_chunks()
    return {
        'enabled': rag_enabled(),
        'llm': llm_configured(),
        'provider': _llm_provider(),
        'model': _chat_model() if llm_configured() else '',
        'indexed_count': len(chunks),
        'updated_at': meta.get('updated_at', ''),
        'with_embeddings': bool(meta.get('with_embeddings')),
    }


def retrieve(question, top_k=5):
    """混合检索：词法匹配 + 可选向量余弦，返回 top_k 片段"""
    chunks = _load_chunks()
    if not chunks:
        return []
    q_emb = embed_text(question) if llm_configured() else None
    scored = []
    for ch in chunks:
        ls = _lexical_score(question, ch.get('text', ''))
        if q_emb and ch.get('embedding'):
            cs = _cosine(q_emb, ch['embedding'])
            score = 0.35 * ls + 0.65 * cs
        else:
            score = ls
        if score > 0:
            scored.append((score, ch))
    scored.sort(key=lambda x: -x[0])
    out = []
    for score, ch in scored[:top_k]:
        item = {k: ch[k] for k in ('id', 'type', 'title', 'text', 'link', 'book_id') if k in ch}
        item['score'] = round(score, 4)
        out.append(item)
    return out


def _template_answer(question, contexts):
    if not contexts:
        return (
            '暂未在平台资料中找到相关内容。你可以尝试在「全部书籍」搜索关键词，'
            '或使用「按课找书」按课程代码查找。'
        )
    lines = ['根据校园书递平台资料整理：', '']
    for i, c in enumerate(contexts, 1):
        title = c.get('title') or c.get('type', '条目')
        snippet = (c.get('text') or '')[:180]
        link = c.get('link') or ''
        lines.append(f'{i}. 【{title}】{snippet}…')
        if link:
            lines.append(f'   链接：{link}')
    lines.append('')
    lines.append('以上信息来自在售书籍、课程教材库与平台说明，价格与库存以详情页为准。')
    return '\n'.join(lines)


def generate_answer(question, contexts):
    """有 LLM 则 RAG 生成；否则模板拼接"""
    if not llm_configured():
        return _template_answer(question, contexts)

    ctx_block = '\n\n'.join(
        f'[{c.get("type")}] {c.get("title")}\n{c.get("text")}\n链接:{c.get("link", "")}'
        for c in contexts
    )
    system = (
        '你是「校园书递」二手教材平台的智能助手。仅根据「参考资料」回答，'
        '不要编造 ISBN、价格、库存。无法从资料得出时明确说明。'
        '回答简洁中文，可列出推荐书籍并注明链接路径。'
    )
    user = f'用户问题：{question}\n\n参考资料：\n{ctx_block or "（无）"}'
    try:
        data = _api_post('/chat/completions', {
            'model': _chat_model(),
            'messages': [
                {'role': 'system', 'content': system},
                {'role': 'user', 'content': user},
            ],
            'temperature': 0.3,
            'max_tokens': 800,
        })
        if data and data.get('choices'):
            return (data['choices'][0].get('message') or {}).get('content', '').strip()
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, KeyError, OSError):
        pass
    return _template_answer(question, contexts)


def ask(question, Book=None, CourseTextbook=None, Announcement=None, top_k=5):
    """AI 助手入口：ensure 索引 → retrieve → generate"""
    if not rag_enabled():
        return {'answer': '智能助手未开启', 'sources': [], 'mode': 'disabled'}
    q = (question or '').strip()
    if len(q) < 2:
        return {'answer': '请输入至少 2 个字的问题', 'sources': [], 'mode': 'invalid'}
    if not _load_chunks() and Book is not None:
        rebuild_index(Book, CourseTextbook, Announcement, with_embeddings=False)
    sources = retrieve(q, top_k=top_k)
    answer = generate_answer(q, sources)
    mode = 'llm' if llm_configured() else 'retrieval'
    return {'answer': answer, 'sources': sources, 'mode': mode}
