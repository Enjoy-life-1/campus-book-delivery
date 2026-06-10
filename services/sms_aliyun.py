"""阿里云短信 SendSms（验证码 / 通知模板）"""
import json
import os


def _settings():
    try:
        from models import Setting
        return Setting.get_all_as_dict()
    except Exception:
        return {}


def _get(key, env_keys, db_key=None):
    """优先读环境变量，其次 Setting 表"""
    for k in env_keys:
        v = (os.environ.get(k) or '').strip()
        if v:
            return v
    if db_key:
        return (_settings().get(db_key) or '').strip()
    return ''


def aliyun_sms_configured():
    """AK/SK + 签名 + 模板均配置才可用"""
    return all([
        _get('access_key_id', ['ALIBABA_CLOUD_ACCESS_KEY_ID', 'SMS_ACCESS_KEY_ID'], 'sms_access_key_id'),
        _get('access_key_secret', ['ALIBABA_CLOUD_ACCESS_KEY_SECRET', 'SMS_ACCESS_KEY_SECRET']),
        _get('sign_name', ['SMS_SIGN_NAME'], 'sms_sign_name'),
        _get('template_code', ['SMS_TEMPLATE_CODE'], 'sms_template_code'),
    ])


def _client():
    from alibabacloud_dysmsapi20170525.client import Client
    from alibabacloud_tea_openapi import models as open_models

    cfg = open_models.Config(
        access_key_id=_get('access_key_id', ['ALIBABA_CLOUD_ACCESS_KEY_ID', 'SMS_ACCESS_KEY_ID'], 'sms_access_key_id'),
        access_key_secret=_get('access_key_secret', ['ALIBABA_CLOUD_ACCESS_KEY_SECRET', 'SMS_ACCESS_KEY_SECRET']),
        endpoint='dysmsapi.aliyuncs.com',
    )
    return Client(cfg)


def send_aliyun_sms(phone, template_code, template_param):
    """template_param: dict，如 {"code": "123456"}"""
    if not aliyun_sms_configured():
        return 'failed', '阿里云短信未配置'
    try:
        from alibabacloud_dysmsapi20170525 import models

        req = models.SendSmsRequest(
            phone_numbers=str(phone),
            sign_name=_get('sign_name', ['SMS_SIGN_NAME'], 'sms_sign_name'),
            template_code=template_code or _get('template_code', ['SMS_TEMPLATE_CODE'], 'sms_template_code'),
            template_param=json.dumps(template_param, ensure_ascii=False),
        )
        resp = _client().send_sms(req)
        body = resp.body
        if body and body.code == 'OK':
            return 'sent', body.biz_id or ''
        msg = (body.message if body else None) or '发送失败'
        code = body.code if body else ''
        return 'failed', f'{code}: {msg}' if code else msg
    except Exception as e:
        return 'failed', str(e)


def send_verify_code(phone, code):
    """注册/登录验证码短信"""
    tpl = _get('template_code', ['SMS_TEMPLATE_CODE'], 'sms_template_code')
    return send_aliyun_sms(phone, tpl, {'code': str(code)})


def send_notify_sms(phone, content):
    """降价/求购等业务通知（需单独通知模板）"""
    tpl = _get('notify_template_code', ['SMS_NOTIFY_TEMPLATE_CODE'], 'sms_notify_template_code')
    if not tpl:
        return 'failed', '未配置 SMS_NOTIFY_TEMPLATE_CODE'
    return send_aliyun_sms(phone, tpl, {'content': (content or '')[:50]})
