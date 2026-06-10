"""密码哈希与校验（兼容旧 MD5，登录后自动升级）"""
import hashlib
import os
import time
from collections import defaultdict  # IP+用户 → 失败时间列表
from threading import Lock
from werkzeug.security import check_password_hash, generate_password_hash

_login_failures = defaultdict(list)  # 无 Redis 时的内存限流
_login_lock = Lock()
_LOGIN_MAX_ATTEMPTS = 10  # 5 分钟内最多失败次数
_LOGIN_WINDOW_SEC = 300
_redis = None
_redis_checked = False


def _get_redis():
    """获取 Redis 客户端单例，失败则返回 None"""
    global _redis, _redis_checked
    if _redis_checked:
        return _redis
    _redis_checked = True
    url = os.environ.get('REDIS_URL', '').strip()
    if not url:
        return None
    try:
        import redis
        _redis = redis.from_url(url, decode_responses=True)
        _redis.ping()
    except Exception:
        _redis = None
    return _redis


def _redis_login_key(username=''):
    """Redis 限流键，与内存版 _login_rate_key 一致"""
    return f'login_fail:{_login_rate_key(username)}'


def hash_password(password):
    """新密码使用 pbkdf2:sha256"""
    return generate_password_hash((password or '').strip(), method='pbkdf2:sha256')


def verify_password(raw_password, stored_hash):
    """校验密码：pbkdf2/scrypt 或旧 MD5 明文比对"""
    raw = (raw_password or '').strip()
    stored = stored_hash or ''
    if stored.startswith('pbkdf2:') or stored.startswith('scrypt:'):
        return check_password_hash(stored, raw)
    return hashlib.md5(raw.encode()).hexdigest() == stored


def password_needs_upgrade(stored_hash):
    """是否为旧 MD5，需登录后升级"""
    s = stored_hash or ''
    return not (s.startswith('pbkdf2:') or s.startswith('scrypt:'))


def _login_rate_key(username=''):
    """限流键：IP + 用户名"""
    try:
        from flask import request
        ip = request.remote_addr or 'unknown'
    except RuntimeError:
        ip = 'unknown'
    user = (username or '').strip().lower()
    return f'{ip}:{user}' if user else ip


def check_login_rate_limit(username=''):
    """登录前检查是否触发限流"""
    r = _get_redis()
    if r:
        try:
            return int(r.get(_redis_login_key(username)) or 0) < _LOGIN_MAX_ATTEMPTS
        except Exception:
            pass
    key = _login_rate_key(username)
    now = time.time()
    with _login_lock:
        times = [t for t in _login_failures.get(key, []) if now - t < _LOGIN_WINDOW_SEC]
        _login_failures[key] = times
        if len(times) >= _LOGIN_MAX_ATTEMPTS:
            return False
    return True


def record_login_failure(username=''):
    """记录一次登录失败"""
    r = _get_redis()
    if r:
        try:
            key = _redis_login_key(username)
            n = r.incr(key)
            if n == 1:
                r.expire(key, _LOGIN_WINDOW_SEC)
            return
        except Exception:
            pass
    key = _login_rate_key(username)
    with _login_lock:
        _login_failures[key].append(time.time())


def clear_login_attempts(username=''):
    """登录成功，清零失败计数"""
    r = _get_redis()
    if r:
        try:
            r.delete(_redis_login_key(username))
        except Exception:
            pass
    key = _login_rate_key(username)
    with _login_lock:
        _login_failures.pop(key, None)
