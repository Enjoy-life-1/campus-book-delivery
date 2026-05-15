#!/bin/bash

echo "============================================================"
echo "校园书递项目 - SQLite 数据库设置和运行"
echo "============================================================"
echo ""

# 检查 Python
echo "[1/4] 检查 Python 环境..."
if ! command -v python3 &> /dev/null; then
    echo "✗ 未找到 Python3，请先安装 Python3"
    exit 1
fi
echo "✓ Python 环境正常"
echo ""

# 安装依赖
echo "[2/4] 安装/更新依赖..."
python3 -m pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "✗ 依赖安装失败"
    exit 1
fi
echo "✓ 依赖安装完成"
echo ""

# 初始化数据库
echo "[3/4] 初始化数据库..."
python3 init_db.py
if [ $? -ne 0 ]; then
    echo "✗ 数据库初始化失败"
    exit 1
fi
echo "✓ 数据库初始化完成"
echo ""

# 迁移数据
echo "[4/4] 检查是否需要迁移数据..."
if [ -f "database/users.json" ]; then
    echo "检测到 JSON 数据文件"
    read -p "是否要迁移数据到 SQLite？(y/n，默认 y): " migrate
    if [ "$migrate" != "n" ]; then
        echo "开始迁移数据..."
        python3 migrate_json_to_sqlite.py
        if [ $? -ne 0 ]; then
            echo "⚠ 数据迁移失败，但可以继续运行应用"
        else
            echo "✓ 数据迁移完成"
        fi
    else
        echo "跳过数据迁移"
    fi
else
    echo "未找到 JSON 数据文件，跳过数据迁移"
fi
echo ""

# 运行应用
echo "============================================================"
echo "启动应用..."
echo "应用将在 http://localhost:5000 启动"
echo "按 Ctrl+C 停止应用"
echo "============================================================"
echo ""

if [ -f "run.py" ]; then
    python3 run.py
else
    python3 app.py
fi

