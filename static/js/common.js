// common.js - 校园书递项目通用工具函数

// API基础URL
const API_BASE_URL = '/api';

// API请求封装
async function apiRequest(endpoint, options = {}) {
    // 确保URL正确拼接，处理斜杠问题
    const url = endpoint.startsWith('/') ? 
        `${API_BASE_URL}${endpoint}` : 
        `${API_BASE_URL}/${endpoint}`;
    console.log('API请求URL:', url);
    console.log('API请求选项:', options);
    
    // 默认选项
    const defaultOptions = {
        headers: {
            'Content-Type': 'application/json'
        },
        credentials: 'include' // 重要：允许跨域请求携带cookies
    };
    
    // 合并选项
    const mergedOptions = {
        ...defaultOptions,
        ...options,
        headers: {
            ...defaultOptions.headers,
            ...options.headers
        }
    };
    
    try {
        const response = await fetch(url, mergedOptions);
        console.log('API响应状态:', response.status);
        
        // 解析响应
        let data;
        try {
            data = await response.json();
            console.log('API响应数据:', data);
        } catch (e) {
            console.error('响应解析错误:', e);
            data = { status: 'error', message: '无效的响应格式' };
        }
        
        // 处理非2xx响应
        if (!response.ok) {
            console.error('API请求失败:', response.status, data);
            throw new Error(data.message || `请求失败: ${response.status}`);
        }
        
        return data;
    } catch (error) {
        // 检查是否是浏览器扩展开发工具相关错误
        const isExtensionDevToolsError = error.message && 
            error.message.includes('Unchecked runtime.lastError') && 
            error.message.includes('can not use with devtools');
            
        if (isExtensionDevToolsError) {
            console.warn('忽略API请求中的浏览器扩展开发工具错误:', error);
            // 返回一个友好的错误对象，不中断应用流程
            return {
                status: 'error',
                message: '操作已继续，忽略了浏览器扩展相关错误'
            };
        }
        
        console.error('API请求错误详情:', error);
        alert(`请求失败: ${error.message}`);
        throw error;
    }
}

// 存储用户信息
function saveUser(userInfo) {
    try {
        localStorage.setItem("currentUser", JSON.stringify(userInfo));
        // 触发storage事件，通知其他页面更新
        window.dispatchEvent(new Event('storage'));
    } catch (e) {
        console.warn('无法保存用户信息:', e);
    }
}

// 获取当前登录用户
function getCurrentUser() {
    try {
        const storedUser = localStorage.getItem("currentUser");
        if (!storedUser) return null;
        
        return JSON.parse(storedUser);
    } catch (e) {
        console.error('获取用户信息时出错:', e);
        return null;
    }
}

// 验证登录状态（未登录跳转登录页）
function checkLogin(redirectUrl) {
    const user = getCurrentUser();
    if (!user) {
        alert("请先登录！");
        // 记录当前页面作为登录后跳转目标
        const targetUrl = redirectUrl || window.location.href;
        window.location.href = `/login?redirect=${encodeURIComponent(targetUrl)}`;
        return false;
    }
    return true;
}

// 退出登录
async function logout() {
    try {
        // 调用后端登出API
        await apiRequest('/logout', {
            method: 'POST'
        });
    } catch (error) {
        console.error('登出API调用失败:', error);
    } finally {
        // 清理本地存储
        localStorage.removeItem('currentUser');
        // 触发storage事件，通知其他页面更新
        window.dispatchEvent(new Event('storage'));
        // 重定向到首页
        window.location.href = '/';
    }
}

// 更新导航栏用户状态
function updateNavbarUserStatus() {
    const user = getCurrentUser();
    const loginSection = document.getElementById('login-section');
    const userSection = document.getElementById('user-section');
    const usernameElement = document.getElementById('username');
    
    if (loginSection && userSection && usernameElement) {
        if (user) {
            loginSection.style.display = 'none';
            userSection.style.display = 'block';
            usernameElement.textContent = user.username;
        } else {
            loginSection.style.display = 'block';
            userSection.style.display = 'none';
        }
    }
}

// 存储书籍数据到localStorage
function saveBook(bookInfo) {
    // 验证登录状态
    if (!checkLogin()) return null;
    
    let booksList = JSON.parse(localStorage.getItem("allBooks")) || [];
    const user = getCurrentUser();
    
    // 补充书籍信息
    bookInfo.id = bookInfo.id || Date.now(); // 编辑时保留原ID
    bookInfo.sellerId = user.id; // 关联卖家ID
    bookInfo.seller = user.username; // 卖家名称
    bookInfo.createTime = bookInfo.createTime || new Date().toLocaleDateString(); // 发布时间
    bookInfo.status = bookInfo.status || "available"; // 默认状态：可售
    
    // 如果是编辑，先移除旧数据
    if (bookInfo.id) {
        booksList = booksList.filter(book => book.id !== bookInfo.id);
    }
    
    // 添加到书籍列表（新书籍放在前面）
    booksList.unshift(bookInfo);
    localStorage.setItem("allBooks", JSON.stringify(booksList));
    
    // 触发storage事件，通知其他页面更新
    window.dispatchEvent(new Event('storage'));
    
    return bookInfo;
}

// 获取所有书籍
function getAllBooks() {
    return JSON.parse(localStorage.getItem("allBooks")) || [];
}

// 根据ID获取书籍详情
function getBookById(bookId) {
    const books = getAllBooks();
    return books.find(book => book.id.toString() === bookId.toString()) || null;
}

// 获取用户发布的书籍
function getUserBooks() {
    const userData = getCurrentUser();
    if (!userData) return [];
    
    // 获取用户ID，处理可能的嵌套结构
    const user = userData.user || userData;
    if (!user || !user.id) return [];
    
    // 使用toString()确保类型一致，避免类型不匹配问题
    const userId = user.id.toString();
    
    return getAllBooks().filter(book => {
        // 安全地获取sellerId并转换为字符串进行比较
        const bookSellerId = book.sellerId ? book.sellerId.toString() : '';
        return bookSellerId === userId;
    });
}

// 收藏书籍
function collectBook(bookId) {
    if (!checkLogin()) return false;
    
    const user = getCurrentUser();
    const collectionKey = `collections_${user.id}`;
    let collections = JSON.parse(localStorage.getItem(collectionKey)) || [];
    
    // 检查是否已收藏
    if (collections.includes(bookId)) {
        alert("已收藏过这本书籍！");
        return false;
    }
    
    collections.push(bookId);
    localStorage.setItem(collectionKey, JSON.stringify(collections));
    alert("收藏成功！");
    // 触发storage事件，通知其他页面更新
    window.dispatchEvent(new Event('storage'));
    return true;
}

// 取消收藏书籍
function uncollectBook(bookId) {
    if (!checkLogin()) return false;
    
    const user = getCurrentUser();
    const collectionKey = `collections_${user.id}`;
    let collections = JSON.parse(localStorage.getItem(collectionKey)) || [];
    
    // 检查是否已收藏
    if (!collections.includes(bookId)) {
        alert("您未收藏这本书籍！");
        return false;
    }
    
    // 过滤掉要移除的书籍ID
    collections = collections.filter(id => id !== bookId);
    localStorage.setItem(collectionKey, JSON.stringify(collections));
    alert('已取消收藏');
    // 触发storage事件，通知其他页面更新
    window.dispatchEvent(new Event('storage'));
    return true;
}

// 获取用户收藏的书籍
function getUserCollections() {
    const user = getCurrentUser();
    if (!user) return [];
    
    const collectionKey = `collections_${user.id}`;
    const collectionIds = JSON.parse(localStorage.getItem(collectionKey)) || [];
    
    // 返回收藏的书籍详情
    return getAllBooks().filter(book => collectionIds.includes(book.id));
}

// 初始化默认书籍数据
function initDefaultBooks() {
    if (!localStorage.getItem("allBooks")) {
        const defaultBooks = [
            {
                id: 1,
                title: "考研数学一真题集（2015-2024）含详细解析",
                category: "postgraduate",
                price: 25.00,
                imgs: ["/static/img/考研数学.jpg"],
                author: "李永乐",
                seller: "学长A",
                sellerId: 1001,
                createTime: "2025-10-20",
                tag: "考研必备",
                status: "available"
            },
            {
                id: 2,
                title: "Python编程：从入门到实践（第二版）",
                category: "professional",
                price: 30.00,
                imgs: ["/static/img/python.jpg"],
                author: "埃里克·马瑟斯",
                seller: "学姐B",
                sellerId: 1002,
                createTime: "2025-10-18",
                tag: "编程入门",
                status: "available"
            },
            {
                id: 3,
                title: "大学物理（第七版）上下册",
                category: "textbook",
                price: 18.00,
                imgs: ["/static/img/大学物理.jpg"],
                author: "马文蔚",
                seller: "学长C",
                sellerId: 1003,
                createTime: "2025-10-15",
                tag: "教材",
                status: "sold"
            },
            {
                id: 4,
                title: "平凡的世界（全三册）",
                category: "literature",
                price: 22.00,
                imgs: ["/static/img/平凡的世界.jpg"],
                author: "路遥",
                seller: "学长F",
                sellerId: 1004,
                createTime: "2025-10-08",
                tag: "经典文学",
                status: "available"
            },
            {
                 id: 5,
                 title: "经济学原理（微观+宏观）",
                 category: "textbook",
                 price: 45.00,
                 imgs: ["/static/img/经济.jpg"],
                 author: "曼昆",
                 seller: "学姐D",
                 createTime: "2025-10-05",
                 contact: "13500135000"
            },
            {
                 id: 6,
                 title: "恋练有词：考研英语词汇",
                 category: "postgraduate",
                 price: 18.00,
                 imgs: ["/static/img/词汇.jpg"],
                 author: "朱伟",
                 seller: "学长H",
                 createTime: "2025-09-25",
                 tag: "词汇必备",
                 contact: "13200132000"
            }
        ];
        
        localStorage.setItem("allBooks", JSON.stringify(defaultBooks));
    }
}

// 注册新用户
function registerUser(userData) {
    // 获取现有用户列表
    let users = JSON.parse(localStorage.getItem('users')) || [];
    
    // 检查手机号是否已注册
    const isPhoneExist = users.some(user => user.phone === userData.phone);
    if (isPhoneExist) {
        alert('该手机号已注册，请更换手机号或直接登录');
        return false;
    }
    
    // 检查用户名是否已存在
    const isUsernameExist = users.some(user => user.username === userData.username);
    if (isUsernameExist) {
        alert('该用户名已被使用，请更换用户名');
        return false;
    }
    
    // 创建新用户（实际项目中应加密密码）
    const newUser = {
        id: Date.now(), // 用时间戳作为唯一ID
        username: userData.username,
        phone: userData.phone,
        password: userData.password, // 实际项目中应使用md5等方式加密
        identity: 'student', // 默认学生身份
        createTime: new Date().toLocaleString()
    };
    
    // 保存新用户到本地存储
    users.push(newUser);
    localStorage.setItem('users', JSON.stringify(users));
    
    return true;
}

// 验证用户登录
function loginUser(username, password) {
    const users = JSON.parse(localStorage.getItem('users')) || [];
    return users.find(user => 
        (user.username === username || user.phone === username) && 
        user.password === password
    ) || null;
}

// 获取分类名称映射
function getCategoryName(category) {
    const categories = {
        'textbook': '教材教辅',
        'postgraduate': '考研资料',
        'literature': '文学小说',
        'professional': '专业书籍',
        'other': '其他书籍'
    };
    return categories[category] || category;
}

// 获取状态文本
function getStatusText(status) {
    const statusMap = {
        'available': '在售',
        'sold': '已售出',
        'pending': '待处理',
        'processing': '处理中',
        'completed': '已完成',
        'cancelled': '已取消',
        'reserved': '已预订',
        'active': '上架',
        'inactive': '下架'
    };
    return statusMap[status] || status;
}

// 获取URL参数
function getUrlParam(key) {
    const params = new URLSearchParams(window.location.search);
    return params.get(key);
}

// 保存聊天消息到localStorage（添加错误处理）
function saveMessage(message) {
    try {
        const messagesKey = `messages_${message.sender}_${message.receiver}_${message.bookId}`;
        let messages = [];
        try {
            const storedMessages = localStorage.getItem(messagesKey);
            messages = storedMessages ? JSON.parse(storedMessages) : [];
        } catch (parseError) {
            console.warn('解析存储的消息失败:', parseError);
        }
        messages.push(message);
        localStorage.setItem(messagesKey, JSON.stringify(messages));
    } catch (e) {
        console.warn('无法保存聊天消息到localStorage:', e);
    }
}

// 获取聊天记录
function getMessages(senderId, receiverId, bookId) {
    // 尝试两种可能的键组合，因为对话双方可能有不同的发送顺序
    const messagesKey1 = `messages_${senderId}_${receiverId}_${bookId}`;
    const messagesKey2 = `messages_${receiverId}_${senderId}_${bookId}`;
    
    const messages1 = JSON.parse(localStorage.getItem(messagesKey1)) || [];
    const messages2 = JSON.parse(localStorage.getItem(messagesKey2)) || [];
    
    // 合并并按时间戳排序
    return [...messages1, ...messages2].sort((a, b) => a.timestamp - b.timestamp);
}

// 更新用户菜单
function updateUserMenu() {
    const userMenu = document.getElementById('userMenu');
    if (!userMenu) return; // 防止页面没有用户菜单元素
    
    const user = getCurrentUser();
    
    if (user) {
        userMenu.innerHTML = `
            <a class="nav-link dropdown-toggle" href="#" role="button" data-bs-toggle="dropdown">
                <i class="fa fa-user-circle text-primary"></i> ${user.user?.username || user.username || '用户'}
            </a>
            <ul class="dropdown-menu dropdown-menu-end">
                <li><a class="dropdown-item" href="/personalCenter">个人中心</a></li>
                <li><a class="dropdown-item" href="/myBooks">我的书籍</a></li>
                <li><a class="dropdown-item" href="/myCollections">我的收藏</a></li>
                <li><hr class="dropdown-divider"></li>
                <li><a class="dropdown-item" href="/login?role=admin"><i class="fa fa-lock"></i> 管理员登录</a></li>
                <li><a class="dropdown-item" href="#" onclick="logout()">退出登录</a></li>
            </ul>
        `;
    } else {
        userMenu.innerHTML = `
            <a class="nav-link dropdown-toggle" href="#" role="button" data-bs-toggle="dropdown">
                <i class="fa fa-user text-primary"></i> 登录/注册
            </a>
            <ul class="dropdown-menu dropdown-menu-end">
                <li><a class="dropdown-item" href="/login">登录</a></li>
                <li><a class="dropdown-item" href="/register">注册</a></li>
                <li><hr class="dropdown-divider"></li>
                <li><a class="dropdown-item" href="/login?role=admin"><i class="fa fa-lock"></i> 管理员登录</a></li>
            </ul>
        `;
    }
}

// 初始化应用
document.addEventListener('DOMContentLoaded', function() {
    initDefaultBooks();
    updateUserMenu(); // 初始化时更新用户菜单
});