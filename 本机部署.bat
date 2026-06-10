@echo off
REM 生产部署：pip install → npm build → bootstrap DB → waitress :5000
chcp 65001 >nul
cd /d "%~dp0"

title 校园书递 - 本机部署



echo ========================================

echo   校园书递 - 本机服务器部署

echo ========================================

echo.



call "%~dp0_python_env.bat"

if errorlevel 1 (

  echo [错误] 未找到 Python

  echo 请安装 Python 3.10+ 并勾选 Add to PATH，或确保 py 启动器可用

  pause

  exit /b 1

)

echo 使用: %PY%

if not exist .env copy .env.example .env



echo [1/4] 安装 Python 依赖...

"%PY%" -m pip install -r requirements.txt -q

if errorlevel 1 (echo [错误] pip 安装失败 & pause & exit /b 1)



echo [2/4] 构建前端...

where node >nul 2>&1

if errorlevel 1 (

  echo [警告] 未找到 Node.js，跳过 npm build（需已有 dist 目录）

) else (

  call npm install --silent

  call npm run build

  if errorlevel 1 (echo [错误] 前端构建失败 & pause & exit /b 1)

)



echo [3/4] 检查数据库...

set FLASK_ENV=production

"%PY%" -c "from app import bootstrap_database,check_database; bootstrap_database(); import sys; sys.exit(0 if check_database() else 1)"

if errorlevel 1 (

  echo [错误] 数据库不可用，请检查 .env 配置或 MySQL 是否已启动

  pause

  exit /b 1

)



echo [4/4] 启动服务...

echo.

echo 局域网管理后台: 启动后见下方 [INFO] 局域网管理后台 地址

echo 若其他设备无法访问，请以管理员运行 开放局域网.bat

echo.

echo 按 Ctrl+C 停止服务

echo ========================================

set FLASK_ENV=production

set HOST=0.0.0.0

set PORT=5000

netsh advfirewall firewall show rule name="CampusBookDelivery-5000" >nul 2>&1

if errorlevel 1 netsh advfirewall firewall add rule name="CampusBookDelivery-5000" dir=in action=allow protocol=TCP localport=5000 >nul 2>&1

"%PY%" scripts\serve_production.py

pause

