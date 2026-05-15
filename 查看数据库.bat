@echo off
chcp 65001 >nul
echo ============================================================
echo 查看 SQLite 数据库数据
echo ============================================================
echo.

REM 检查Python是否可用
python --version >nul 2>&1
if errorlevel 1 (
    echo ✗ 未检测到 Python，请先安装 Python
    echo.
    echo 提示：请从 https://www.python.org 下载并安装 Python
    pause
    exit /b 1
)

REM 检查数据库文件位置（可能在根目录或instance文件夹）
set DB_ROOT=campus_book_delivery.db
set DB_INSTANCE=instance\campus_book_delivery.db
set DB_FOUND=0

if exist "%DB_ROOT%" (
    set DB_FOUND=1
    echo ✓ 找到数据库文件: %DB_ROOT%
) else if exist "%DB_INSTANCE%" (
    set DB_FOUND=1
    echo ✓ 找到数据库文件: %DB_INSTANCE%
) else (
    echo ✗ 数据库文件不存在
    echo   检查路径: %DB_ROOT%
    echo   检查路径: %DB_INSTANCE%
    echo.
    echo 正在自动初始化数据库...
    python init_db.py
    if errorlevel 1 (
        echo.
        echo ✗ 数据库初始化失败
        echo   请手动运行: python init_db.py
        pause
        exit /b 1
    )
    echo ✓ 数据库初始化完成
    echo.
)

echo.
echo 请选择查看方式：
echo   1. 快速查看（概览，推荐）
echo   2. 自动初始化并查看
echo.
set /p choice="请输入选项 (1-2，默认 1): "

if "%choice%"=="" set choice=1

if "%choice%"=="2" (
    python init_and_view.py
    if errorlevel 1 (
        echo.
        echo ✗ 查看数据库时出错
        pause
        exit /b 1
    )
) else (
    python view_database_simple.py
    if errorlevel 1 (
        echo.
        echo ✗ 查看数据库时出错
        pause
        exit /b 1
    )
)

echo.
pause

