@echo off
chcp 65001 >nul
echo ============================================================
echo 校园书递项目 - SQLite 数据库设置和运行
echo ============================================================
echo.

echo [1/4] 检查 Python 环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo ✗ 未找到 Python，请先安装 Python
    pause
    exit /b 1
)
echo ✓ Python 环境正常
echo.

echo [2/4] 安装/更新依赖...
python -m pip install -r requirements.txt
if errorlevel 1 (
    echo ✗ 依赖安装失败
    pause
    exit /b 1
)
echo ✓ 依赖安装完成
echo.

echo [3/4] 初始化数据库...
python init_db.py
if errorlevel 1 (
    echo ✗ 数据库初始化失败
    pause
    exit /b 1
)
echo ✓ 数据库初始化完成
echo.

echo [4/4] 检查是否需要迁移数据...
if exist "database\users.json" (
    echo 检测到 JSON 数据文件
    set /p migrate="是否要迁移数据到 SQLite？(y/n，默认 y): "
    if /i "%migrate%"=="n" (
        echo 跳过数据迁移
    ) else (
        echo 开始迁移数据...
        python migrate_json_to_sqlite.py
        if errorlevel 1 (
            echo ⚠ 数据迁移失败，但可以继续运行应用
        ) else (
            echo ✓ 数据迁移完成
        )
    )
) else (
    echo 未找到 JSON 数据文件，跳过数据迁移
)
echo.

echo ============================================================
echo 启动应用...
echo 应用将在 http://localhost:5000 启动
echo 按 Ctrl+C 停止应用
echo ============================================================
echo.

if exist "run.py" (
    python run.py
) else (
    python app.py
)

pause

