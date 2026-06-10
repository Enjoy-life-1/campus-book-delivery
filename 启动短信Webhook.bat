@echo off
REM 本地短信 Webhook 接收器 :8080，配合 .env 中 SMS_WEBHOOK_URL
chcp 65001 >nulcd /d "%~dp0"
title 校园书递 - 短信 Webhook 8080

call "%~dp0_python_env.bat"
if errorlevel 1 (echo [错误] 未找到 Python & pause & exit /b 1)

echo ========================================
echo   短信 Webhook 接收服务
echo   http://127.0.0.1:8080/sms
echo ========================================
echo 校园书递管理后台填: http://127.0.0.1:8080/sms
echo 验证码会打印在本窗口和 logs\sms_webhook.log
echo 按 Ctrl+C 停止
echo.

"%PY%" scripts\sms_webhook_server.py
pause
