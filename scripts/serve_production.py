#!/usr/bin/env python3
"""本机生产模式启动（Windows 用 Waitress，Linux 可改用 gunicorn）"""
import os
import socket
import sys

from _root import ROOT, setup

setup()


def _ensure_secret_key():
    env_path = os.path.join(ROOT, '.env')
    if not os.path.exists(env_path):
        return
    text = open(env_path, encoding='utf-8').read()
    bad = (
        'SECRET_KEY=请替换为随机长字符串',
        'SECRET_KEY=your-secret-key',
        'SECRET_KEY=',
    )
    if not any(x in text for x in bad):
        return
    import secrets
    key = secrets.token_hex(32)
    lines = []
    replaced = False
    for line in text.splitlines():
        if line.strip().startswith('SECRET_KEY='):
            lines.append(f'SECRET_KEY={key}')
            replaced = True
        else:
            lines.append(line)
    if not replaced:
        lines.append(f'SECRET_KEY={key}')
    open(env_path, 'w', encoding='utf-8').write('\n'.join(lines) + '\n')
    print('[INFO] 已自动生成 SECRET_KEY 并写入 .env')


def _local_ips():
    ips = []
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ips.append(s.getsockname()[0])
        s.close()
    except OSError:
        pass
    return ips


def main():
    os.environ.setdefault('FLASK_ENV', 'production')
    _ensure_secret_key()

    from app import app, bootstrap_database, check_database

    bootstrap_database()
    if not check_database():
        sys.exit(1)
    from app import check_security_warnings
    check_security_warnings()

    host = os.environ.get('HOST', '0.0.0.0')
    port = int(os.environ.get('PORT', '5000'))
    threads = int(os.environ.get('WAITRESS_THREADS', '8'))

    print('[INFO] 生产模式启动')
    print(f'[INFO] 本机访问: http://127.0.0.1:{port}')
    ips = _local_ips()
    for ip in ips:
        print(f'[INFO] 局域网用户端: http://{ip}:{port}')
        print(f'[INFO] 局域网管理后台: http://{ip}:{port}/admin/login')
    if not ips:
        print(f'[INFO] 局域网管理后台: http://<本机IP>:{port}/admin/login')
    print(f'[INFO] 管理后台(本机): http://127.0.0.1:{port}/admin/login')

    if sys.platform == 'win32':
        # Windows 本机部署：Flask 多线程（支持 WebSocket / 私信）
        app.run(debug=False, use_reloader=False, host=host, port=port, threaded=True)
    else:
        from waitress import serve
        serve(app, host=host, port=port, threads=threads)


if __name__ == '__main__':
    main()
