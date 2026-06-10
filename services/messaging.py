"""私信 WebSocket 推送（flask-sock）"""
import json
import threading

from flask import session
from flask_sock import Sock

sock = Sock()  # flask-sock 全局实例
_lock = threading.Lock()  # 保护 _peers 字典
_peers = {}  # ws 连接 → {user_id, conv_ids}


def register_chat_sock(app):
    """注册 WebSocket 路由 /ws/chat"""
    sock.init_app(app)

    @sock.route('/ws/chat')
    def chat_socket(ws):
        """Messages.vue 连接；subscribe/unsubscribe 按 conv_id 收推送"""
        if 'user_id' not in session:  # 握手时校验 Session Cookie
            ws.send(json.dumps({'type': 'error', 'message': '未登录'}, ensure_ascii=False))
            return
        uid = str(session['user_id'])
        subs = set()  # 本连接订阅的会话 ID
        with _lock:
            _peers[ws] = {'user_id': uid, 'conv_ids': subs}
        try:
            ws.send(json.dumps({'type': 'connected', 'user_id': uid}, ensure_ascii=False))
            while True:
                raw = ws.receive()
                if raw is None:
                    break  # 连接关闭
                try:
                    msg = json.loads(raw)
                except json.JSONDecodeError:
                    continue
                mtype = msg.get('type')
                if mtype == 'subscribe':  # 进入会话页时订阅
                    cid = str(msg.get('conv_id', ''))
                    if cid:
                        subs.add(cid)
                elif mtype == 'unsubscribe':  # 离开会话页
                    cid = str(msg.get('conv_id', ''))
                    subs.discard(cid)
                elif mtype == 'ping':  # 心跳
                    ws.send(json.dumps({'type': 'pong'}, ensure_ascii=False))
        finally:
            with _lock:
                _peers.pop(ws, None)  # 断开清理


def push_chat_event(conv_id, payload, exclude_user=None):
    """HTTP 发消息后调用，向在线订阅者推送（type: message / read 等）"""
    data = json.dumps(payload, ensure_ascii=False)
    cid = str(conv_id)
    with _lock:
        targets = [
            (ws, info) for ws, info in list(_peers.items())
            if cid in info.get('conv_ids', set()) and info.get('user_id') != exclude_user
        ]
    for ws, _ in targets:
        try:
            ws.send(data)
        except Exception:
            pass  # 连接已断则忽略
