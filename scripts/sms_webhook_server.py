#!/usr/bin/env python3
"""本地短信 Webhook 接收服务 — 校园书递 POST 到此，开发环境打印/落盘验证码"""
import json
import os
import re
import time
from http.server import BaseHTTPRequestHandler, HTTPServer

from _root import ROOT, setup

setup()
LOG_FILE = os.path.join(ROOT, 'logs', 'sms_webhook.log')
HOST = os.environ.get('SMS_WEBHOOK_HOST', '127.0.0.1')
PORT = int(os.environ.get('SMS_WEBHOOK_PORT', '8080'))
_last = []


def _log(msg):
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    line = f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n"
    print(line, end='')
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(line)


class Handler(BaseHTTPRequestHandler):
    """接收 POST /sms：解析验证码写入 log"""

    def log_message(self, fmt, *args):
        pass

    def _json(self, code, data):
        body = json.dumps(data, ensure_ascii=False).encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path.rstrip('/') in ('', '/sms', '/health'):
            self._json(200, {'ok': True, 'service': 'sms-webhook', 'recent': _last[-10:]})
            return
        self._json(404, {'ok': False, 'message': 'not found'})

    def do_POST(self):
        # body: { phone, title, content }，正则提取 6 位验证码
        if self.path.rstrip('/') != '/sms':
            self._json(404, {'ok': False, 'message': 'POST /sms only'})
            return
        n = int(self.headers.get('Content-Length', 0))
        raw = self.rfile.read(n).decode('utf-8') if n else '{}'
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            self._json(400, {'ok': False, 'message': 'invalid json'})
            return
        phone = str(data.get('phone', '')).strip()
        title = str(data.get('title', '')).strip()
        content = str(data.get('content', '')).strip()
        code = ''
        m = re.search(r'(\d{6})', content)
        if m:
            code = m.group(1)
        rec = {'phone': phone, 'title': title, 'content': content, 'code': code, 'at': time.strftime('%H:%M:%S')}
        _last.append(rec)
        if len(_last) > 50:
            _last.pop(0)
        _log(f"SMS -> {phone} | {title} | {content}" + (f" | 验证码={code}" if code else ''))
        self._json(200, {'ok': True, 'phone': phone, 'code': code})


def main():
    srv = HTTPServer((HOST, PORT), Handler)
    _log(f'短信 Webhook 已启动 http://{HOST}:{PORT}/sms')
    _log(f'日志文件: {LOG_FILE}')
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        _log('已停止')


if __name__ == '__main__':
    main()
