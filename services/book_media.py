"""书籍图片：本地或 OSS 存储，替代 base64 入库"""
import base64
import os
import re

from .oss_storage import oss_enabled, upload_bytes as oss_upload_bytes

BOOK_IMAGE_EXT = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
BOOK_UPLOAD_SUBDIR = ('static', 'uploads', 'books')
AVATAR_UPLOAD_SUBDIR = ('static', 'uploads', 'avatars')


def book_upload_dir(app):
    path = os.path.join(app.root_path, *BOOK_UPLOAD_SUBDIR)
    os.makedirs(path, exist_ok=True)
    return path


def save_book_image_file(app, raw: bytes, ext: str, generate_id) -> str:
    """保存书籍图：OSS 优先，否则 static/uploads/books"""
    ext = (ext or 'jpg').lower()
    if ext == 'jpeg':
        ext = 'jpg'
    if ext not in BOOK_IMAGE_EXT:
        ext = 'jpg'
    if len(raw) > 5 * 1024 * 1024:
        raise ValueError('图片不能超过 5MB')
    fname = f'{generate_id()}.{ext}'
    if oss_enabled():
        prefix = (os.environ.get('OSS_PREFIX') or 'books').strip('/')
        key = f'{prefix}/{fname}'
        return oss_upload_bytes(raw, ext, key)
    path = os.path.join(book_upload_dir(app), fname)
    with open(path, 'wb') as f:
        f.write(raw)
    return f'/static/uploads/books/{fname}'


def avatar_upload_dir(app):
    path = os.path.join(app.root_path, *AVATAR_UPLOAD_SUBDIR)
    os.makedirs(path, exist_ok=True)
    return path


def save_avatar_file(app, raw: bytes, ext: str, generate_id) -> str:
    ext = (ext or 'jpg').lower()
    if ext == 'jpeg':
        ext = 'jpg'
    if ext not in BOOK_IMAGE_EXT:
        ext = 'jpg'
    if len(raw) > 2 * 1024 * 1024:
        raise ValueError('头像不能超过 2MB')
    fname = f'{generate_id()}.{ext}'
    if oss_enabled():
        prefix = (os.environ.get('OSS_PREFIX') or 'avatars').strip('/')
        key = f'{prefix}/{fname}'
        return oss_upload_bytes(raw, ext, key)
    path = os.path.join(avatar_upload_dir(app), fname)
    with open(path, 'wb') as f:
        f.write(raw)
    return f'/static/uploads/avatars/{fname}'


def normalize_avatar_url(url: str) -> str:
    u = (url or '').strip()
    if not u:
        return ''
    if u.startswith('data:image'):
        return u if len(u) >= 1000 else ''
    if u.startswith('/static/') or u.startswith('http://') or u.startswith('https://'):
        return u
    return ''


def save_avatar_data_url(app, data_url: str, generate_id) -> str:
    m = re.match(r'^data:image/([\w+]+);base64,(.+)$', (data_url or '').strip(), re.I)
    if not m:
        return data_url
    ext = m.group(1).lower()
    if ext == 'svg+xml':
        raise ValueError('不支持 SVG')
    raw = base64.b64decode(m.group(2))
    return save_avatar_file(app, raw, ext, generate_id)


def persist_data_url(app, data_url: str, generate_id) -> str:
    m = re.match(r'^data:image/([\w+]+);base64,(.+)$', (data_url or '').strip(), re.I)
    if not m:
        return data_url
    ext = m.group(1).lower()
    if ext == 'svg+xml':
        raise ValueError('不支持 SVG')
    raw = base64.b64decode(m.group(2))
    return save_book_image_file(app, raw, ext, generate_id)


def normalize_book_images(app, imgs, generate_id):
    """发布时将 data URL 转为持久化 URL 列表"""
    if not imgs:
        return []
    if isinstance(imgs, str):
        imgs = [imgs]
    out = []
    for item in imgs:
        u = (item or '').strip()
        if not u:
            continue
        if u.startswith('data:image'):
            u = persist_data_url(app, u, generate_id)
        out.append(u)
    return out


def register_book_media(app, generate_id):
    """注册 POST /api/books/upload-image"""
    @app.route('/api/books/upload-image', methods=['POST'])
    def upload_book_image():
        """multipart 单张上传，返回 { url }"""
        from flask import jsonify, request, session

        if 'user_id' not in session:
            return jsonify({'status': 'error', 'message': '请先登录'}), 401
        f = request.files.get('file')
        if not f or not f.filename:
            return jsonify({'status': 'error', 'message': '请选择图片'}), 400
        ext = f.filename.rsplit('.', 1)[-1].lower() if '.' in f.filename else 'jpg'
        if ext not in BOOK_IMAGE_EXT:
            return jsonify({'status': 'error', 'message': '仅支持 png/jpg/gif/webp'}), 400
        try:
            url = save_book_image_file(app, f.read(), ext, generate_id)
        except ValueError as e:
            return jsonify({'status': 'error', 'message': str(e)}), 400
        return jsonify({'status': 'success', 'url': url})
