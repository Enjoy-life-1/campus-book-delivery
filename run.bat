@echo off
REM 开发模式：Flask :5000 + Vite :5173（浏览器访问 5173）
chcp 65001 >nulcd /d "%~dp0"
title 校园书递 - 开发启动

call "%~dp0_python_env.bat"
if errorlevel 1 (
  echo [错误] 未找到 Python 3.10+
  pause
  exit /b 1
)

where node >nul 2>&1
if errorlevel 1 (
  echo [错误] 未找到 Node.js，请先安装 Node.js
  pause
  exit /b 1
)

if not exist node_modules call npm install --silent
if not exist .env if exist .env.example copy .env.example .env >nul

echo [INFO] 启动 Flask :5000 ...
start "校园书递-Flask" cmd /k "%PY%" app.py

echo [INFO] 启动 Vite  :5173 ...
echo [INFO] 浏览器打开 http://localhost:5173
echo [INFO] 管理后台   http://localhost:5173/admin/login
echo [INFO] 账号 admin/admin123  student1/student123
echo.
npm run dev
