"""手机验证码校验（Flask session 存储）"""
import time


def verify_phone_code(phone, code, session_store, sms_gateway_on):
    """校验注册/登录验证码；开发环境无短信时可 666666"""
    import os
    code = (code or '').strip()
    phone = (phone or '').strip()
    if not code:
        return False, '请输入验证码'
    codes = session_store.get('verification_codes', {})
    dev_code_ok = (
        not sms_gateway_on
        and os.environ.get('FLASK_ENV', '').lower() != 'production'
    )
    if code == '666666':
        if dev_code_ok:
            return True, ''
        return False, '请使用短信收到的验证码'
    info = codes.get(phone)
    if not info:
        return False, '请先获取验证码'
    if time.time() > info.get('expire_time', 0):
        return False, '验证码已过期，请重新获取'
    if info.get('code') != code:
        return False, '验证码错误'
    return True, ''
