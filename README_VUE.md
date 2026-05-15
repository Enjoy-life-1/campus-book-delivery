# 校园书递项目 - Vue前端迁移说明

## 项目结构

```
项目根目录/
├── src/                    # Vue源代码目录
│   ├── assets/            # 静态资源
│   │   └── css/           # 样式文件
│   ├── components/        # Vue组件
│   │   └── Navbar.vue     # 导航栏组件
│   ├── router/            # 路由配置
│   │   └── index.js       # 路由定义
│   ├── utils/             # 工具函数
│   │   ├── api.js         # API封装
│   │   ├── auth.js        # 认证工具
│   │   └── helpers.js     # 辅助函数
│   ├── views/             # 页面组件
│   │   ├── Home.vue       # 首页
│   │   ├── Login.vue      # 登录页
│   │   ├── Register.vue   # 注册页
│   │   ├── BooksList.vue  # 书籍列表
│   │   └── admin/         # 管理员页面
│   ├── App.vue            # 根组件
│   └── main.js            # 入口文件
├── static/                # 原有静态文件（保留）
├── templates/             # 原有HTML模板（保留）
├── app.py                 # Flask后端（已更新支持Vue SPA）
├── package.json           # npm依赖配置
├── vite.config.js         # Vite构建配置
└── index.html             # Vue应用入口HTML
```

## 安装和运行

### 1. 安装依赖

```bash
npm install
```

### 2. 开发模式运行

```bash
# 启动Vue开发服务器（端口5173）
npm run dev

# 在另一个终端启动Flask后端（端口5000）
python app.py
```

### 3. 构建生产版本

```bash
npm run build
```

构建后的文件会在 `dist/` 目录中。Flask后端会自动服务这些文件。

## 主要特性

1. **Vue 3 + Composition API**: 使用最新的Vue 3语法
2. **Vue Router**: 单页应用路由管理
3. **Axios**: HTTP请求库，已配置拦截器
4. **Vite**: 快速的构建工具
5. **响应式设计**: 保持原有的Bootstrap样式

## API集成

所有API调用都封装在 `src/utils/api.js` 中，包括：
- 认证API（登录、注册、登出）
- 书籍API（获取、添加、更新、删除）
- 订单API
- 收藏API
- 购物车API
- 管理员API

## 路由说明

- `/` - 首页
- `/login` - 登录页
- `/register` - 注册页
- `/booksList` - 书籍列表
- `/book/:id` - 书籍详情
- `/publishBook` - 发布书籍
- `/admin` - 管理员后台

## 注意事项

1. **开发模式**: Vue开发服务器运行在5173端口，通过代理访问Flask API（5000端口）
2. **生产模式**: 构建后的文件由Flask服务，所有路由都会返回index.html，由Vue Router处理
3. **认证**: 使用localStorage存储用户信息，路由守卫会自动检查登录状态
4. **样式**: 原有的CSS文件已保留，通过 `src/assets/css/main.css` 引入

## 后续开发

目前已完成：
- ✅ 项目基础结构
- ✅ 路由配置
- ✅ API封装
- ✅ 首页和登录页
- ✅ 导航栏组件
- ✅ Flask后端SPA支持

待完善：
- ⏳ 其他页面的完整实现
- ⏳ 状态管理（可考虑引入Pinia）
- ⏳ 更多可复用组件
- ⏳ 错误处理和加载状态优化

