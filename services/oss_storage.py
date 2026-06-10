"""可选阿里云 OSS 图片存储；未配置时由 book_media 走本地目录"""
import os


def oss_enabled():
    """USE_OSS=1 且 AK/SK/Bucket/Endpoint 齐全"""
    if os.environ.get('USE_OSS', '').lower() not in ('1', 'true', 'yes'):
        return False
    return bool(
        os.environ.get('OSS_ACCESS_KEY_ID')
        and os.environ.get('OSS_ACCESS_KEY_SECRET')
        and os.environ.get('OSS_BUCKET')
        and os.environ.get('OSS_ENDPOINT')
    )


def upload_bytes(raw: bytes, ext: str, object_key: str) -> str:
    """上传二进制到 OSS，返回公网 URL"""
    try:
        import oss2
    except ImportError as e:
        raise RuntimeError('请安装 oss2: pip install oss2') from e

    auth = oss2.Auth(
        os.environ['OSS_ACCESS_KEY_ID'],
        os.environ['OSS_ACCESS_KEY_SECRET'],
    )
    bucket = oss2.Bucket(
        auth,
        os.environ['OSS_ENDPOINT'],
        os.environ['OSS_BUCKET'],
    )
    bucket.put_object(object_key, raw)
    base = (os.environ.get('OSS_PUBLIC_BASE') or '').strip().rstrip('/')
    if base:
        return f'{base}/{object_key}'
    return f'https://{os.environ["OSS_BUCKET"]}.{os.environ["OSS_ENDPOINT"]}/{object_key}'
