import os
import sys
from app import app

if __name__ == '__main__':
    # 设置环境变量
    os.environ['FLASK_ENV'] = 'development'
    os.environ['FLASK_APP'] = 'app.py'
    
    # 启动应用
    print('启动校园图书配送系统...')
    print('访问地址: http://localhost:5000')
    print('API地址: http://localhost:5000/api')
    print('按 Ctrl+C 停止服务')
    
    # 启用调试模式以确保修改立即生效
    app.run(host='0.0.0.0', port=5000, debug=True)