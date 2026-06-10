@echo off
REM 添加入站防火墙规则 TCP 5000，并打印局域网访问地址
chcp 65001 >nulcd /d "%~dp0"
title 校园书递 - 开放局域网访问

echo ========================================
echo   开放局域网访问（端口 5000）
echo ========================================
echo.

netsh advfirewall firewall show rule name="CampusBookDelivery-5000" >nul 2>&1
if errorlevel 1 (
  netsh advfirewall firewall add rule name="CampusBookDelivery-5000" dir=in action=allow protocol=TCP localport=5000
  if errorlevel 1 (
    echo [错误] 防火墙规则添加失败，请右键「以管理员身份运行」本脚本
    pause
    exit /b 1
  )
  echo [OK] 已添加防火墙入站规则 TCP 5000
) else (
  echo [OK] 防火墙规则已存在
)

echo.
call "%~dp0_python_env.bat" 2>nul
if not errorlevel 1 (
  "%PY%" -c "import socket;s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM);s.connect(('8.8.8.8',80));ip=s.getsockname()[0];s.close();print(f'局域网管理后台: http://{ip}:5000/admin/login');print(f'局域网用户端:   http://{ip}:5000')"
) else (
  echo 局域网管理后台: http://^<本机IP^>:5000/admin/login
)
echo.
echo 请先运行 本机部署.bat 启动服务，同一 WiFi/局域网内其他设备用上述地址访问
pause
