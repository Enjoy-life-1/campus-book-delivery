// 全局变量
let allBooks = [];
let filteredBooks = [];
let currentPage = 1;
const booksPerPage = 8;

// 转义HTML特殊字符的函数
function escapeHtml(unsafe) {
    if (unsafe === undefined || unsafe === null) {
        return '';
    }
    return String(unsafe)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

// 防抖函数
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// 滚动动画观察器
function initScrollAnimations() {
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    
    const observer = new IntersectionObserver(function(entries) {
        entries.forEach((entry, index) => {
            if (entry.isIntersecting) {
                setTimeout(() => {
                    entry.target.style.opacity = '1';
                    entry.target.style.transform = 'translateY(0)';
                }, index * 50);
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);
    
    // 观察所有书籍卡片
    const bookCards = document.querySelectorAll('.card');
    bookCards.forEach((card, index) => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(30px)';
        card.style.transition = `opacity 0.6s ease ${index * 0.05}s, transform 0.6s ease ${index * 0.05}s`;
        observer.observe(card);
    });
}

// 页面加载完成后执行
document.addEventListener('DOMContentLoaded', function() {
    initPage();
});

function initPage() {
    // 先更新用户菜单（显示登录/用户名）
    updateUserMenu();

    // 解析 URL 参数，支持 ?category=... & keyword=...
    const params = new URLSearchParams(window.location.search);
    const urlCategory = params.get('category') || '';
    const urlKeyword = params.get('keyword') || '';

    if (urlCategory) {
        const el = document.getElementById('categoryFilter');
        if (el) el.value = urlCategory;
    }
    if (urlKeyword) {
        const el = document.getElementById('searchInput');
        if (el) el.value = urlKeyword;
    }

    // 绑定筛选按钮
    const filterBtn = document.getElementById('filterBtn');
    if (filterBtn) {
        filterBtn.addEventListener('click', function (e) {
            e.preventDefault();
            applyFilters();
        });
    }

    // 支持在搜索输入框按 Enter 触发筛选，以及实时搜索（带防抖）
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        // 实时搜索（输入时自动触发，300ms防抖）
        searchInput.addEventListener('input', debounce(() => {
            applyFilters();
        }, 300));
        
        // 支持按 Enter 键立即搜索
        searchInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                applyFilters();
            }
        });
    }
    
    // 筛选器变化时自动触发筛选
    const categoryFilter = document.getElementById('categoryFilter');
    const priceFilter = document.getElementById('priceFilter');
    const timeFilter = document.getElementById('timeFilter');
    
    if (categoryFilter) {
        categoryFilter.addEventListener('change', applyFilters);
    }
    if (priceFilter) {
        priceFilter.addEventListener('change', applyFilters);
    }
    if (timeFilter) {
        timeFilter.addEventListener('change', applyFilters);
    }

    // 加载书籍数据并渲染（loadBooks 会调用 applyFilters -> renderBooks）
    loadBooks();

    // 监听 localStorage 变化（包括页面内手动 dispatch 的 storage 事件），统一刷新用户菜单与书籍列表
    window.addEventListener('storage', function (e) {
        // 为了兼容 window.dispatchEvent(new Event('storage'))（该事件没有 key），这里直接刷新
        updateUserMenu();
        loadBooks();
    });
}

// 加载书籍数据
function loadBooks() {
    // 显示加载状态
    const container = document.getElementById('booksContainer');
    container.innerHTML = '<div class="loading">加载中...</div>';
    
    // 构建查询参数
    const params = new URLSearchParams();
    params.set('page_size', '1000'); // 获取足够多的书籍进行前端筛选
    params.set('_t', new Date().getTime()); // 添加时间戳防止缓存
    
    // 发送API请求获取书籍数据
    fetch(`/api/books?${params.toString()}`, {
        credentials: 'include'
    })
        .then(response => {
            if (!response.ok) {
                throw new Error('网络响应失败');
            }
            return response.json();
        })
        .then(data => {
            if (data.status === 'success') {
                // 从API响应中获取书籍数据（API返回的是books字段）
                const booksFromAPI = data.books || [];
                
                // 数据字段映射和标准化，确保与前端期望的格式一致
                allBooks = booksFromAPI
                    .filter(book => book.status === 'available') // 只显示在售的书籍，已售出的不显示
                    .map(book => ({
                        id: book.id || '',
                        title: book.title || '未知书名',
                        author: book.author || '未知作者',
                        category: book.category || '',
                        price: parseFloat(book.price || 0),
                        stock: book.stock !== undefined ? book.stock : (book.status === 'available' ? 1 : 0),
                        createTime: book.created_at || book.createTime || book.publish_date || '',
                        description: book.description || '',
                        imgs: (() => {
                            if (book.cover_url) return [book.cover_url];
                            if (Array.isArray(book.imgs) && book.imgs.length > 0) return book.imgs;
                            if (book.image) return [book.image];
                            return ['https://picsum.photos/id/48/400/300'];
                        })(),
                        seller: book.owner_name || book.seller || '匿名用户',
                        contact: book.contact || '未提供联系方式',
                        tag: book.category || '',
                        status: book.status || 'available'
                    }));
                
                // 应用筛选条件
                applyFilters();
            } else {
                console.error('获取书籍失败:', data.message);
                // 显示错误信息
                container.innerHTML = '<div class="error">获取书籍失败：' + (data.message || '未知错误') + '</div>';
            }
        })
        .catch(error => {
            console.error('获取书籍出错:', error);
            // 显示错误信息
            container.innerHTML = '<div class="error">网络错误，请检查您的网络连接</div>';
        });
}

// 强制刷新书籍列表（供其他页面或组件调用）
window.refreshBooksList = function() {
    loadBooks();
};

// 分类映射：英文代码 -> 中文分类名称
const categoryMap = {
    'textbook': '教材教辅',
    'postgraduate': '考研资料',
    'literature': '文学小说',
    'professional': '专业书籍',
    'other': '其他书籍'
};

// 应用筛选条件
function applyFilters() {
    const category = document.getElementById('categoryFilter').value;
    const priceRange = document.getElementById('priceFilter').value;
    const timeRange = document.getElementById('timeFilter').value;
    const searchKeyword = document.getElementById('searchInput').value.toLowerCase();
    
    // 重置当前页
    currentPage = 1;
    
    // 筛选书籍
    filteredBooks = allBooks.filter(book => {
        // 只显示在售的书籍
        if (book.status !== 'available') {
            return false;
        }
        
        // 分类筛选 - 直接比较英文代码
        if (category && book.category !== category) {
            return false;
        }
        
        // 价格筛选
        if (priceRange) {
            const price = parseFloat(book.price || 0);
            if (priceRange === '50+') {
                if (price < 50) return false;
            } else {
                const [min, max] = priceRange.split('-').map(Number);
                if (!(price >= min && price <= max)) {
                    return false;
                }
            }
        }
        
        // 时间筛选
        if (timeRange && book.createTime) {
            try {
                // 处理不同的日期格式：YYYY-MM-DD 或 YYYY-MM-DD HH:MM:SS
                let bookDate;
                if (book.createTime.includes(' ')) {
                    bookDate = new Date(book.createTime);
                } else {
                    // 如果是 YYYY-MM-DD 格式，添加时间部分
                    bookDate = new Date(book.createTime + ' 00:00:00');
                }
                
                if (isNaN(bookDate.getTime())) {
                    // 如果日期无效，跳过时间筛选
                    return true;
                }
                
                const now = new Date();
                let days;
                
                switch(timeRange) {
                    case 'week':
                        days = 7;
                        break;
                    case 'month':
                        days = 30;
                        break;
                    case '3month':
                        days = 90;
                        break;
                    default:
                        return true;
                }
                
                const timeDiff = now - bookDate;
                const daysDiff = timeDiff / (1000 * 60 * 60 * 24);
                
                if (daysDiff > days || daysDiff < 0) return false;
            } catch (e) {
                // 日期解析失败，跳过时间筛选
                console.warn('日期解析失败:', book.createTime, e);
            }
        }
        
        // 搜索筛选
        if (searchKeyword) {
            const title = (book.title || '').toLowerCase();
            const author = (book.author || '').toLowerCase();
            const seller = (book.seller || '').toLowerCase();
            
            if (!title.includes(searchKeyword) && 
                !author.includes(searchKeyword) &&
                !seller.includes(searchKeyword)) {
                return false;
            }
        }
        
        return true;
    });
    
    // 渲染书籍列表
    renderBooks();
    
    // 渲染分页
    renderPagination();
}

// 渲染书籍列表
function renderBooks() {
    const container = document.getElementById('booksContainer');
    const noResult = document.getElementById('noResult');
    
    // 计算当前页显示的书籍
    const startIndex = (currentPage - 1) * booksPerPage;
    const endIndex = startIndex + booksPerPage;
    const currentBooks = filteredBooks.slice(startIndex, endIndex);
    
    // 显示无结果提示
    if (filteredBooks.length === 0) {
        noResult.style.display = 'block';
        container.innerHTML = '';
        document.getElementById('pagination').style.display = 'none';
        return;
    }
    
    noResult.style.display = 'none';
    document.getElementById('pagination').style.display = 'flex';
    
    let html = '';
    currentBooks.forEach(book => {
        // 使用common.js中的getCategoryName函数
        const categoryName = typeof getCategoryName === 'function' ? getCategoryName(book.category) : '其他书籍';
        const bookTag = escapeHtml(categoryName.replace(/[^\u4e00-\u9fa5a-zA-Z0-9]/g, ''));
        const bookImage = book.imgs && book.imgs.length > 0 ? book.imgs[0] : 'https://picsum.photos/id/48/400/300';
        const bookPrice = parseFloat(book.price || 0).toFixed(2);
        
        html += `
            <div class="col-md-4 col-sm-6">
                <a href="/book1?id=${encodeURIComponent(book.id)}" class="text-decoration-none">
                    <div class="card">
                        <img src="${escapeHtml(bookImage)}" class="card-img-top" alt="${escapeHtml(book.title)}" loading="lazy">
                        <div class="card-body">
                            <h5 class="card-title">${escapeHtml(book.title)}</h5>
                            <div class="card-author">
                                <i class="fa fa-pencil"></i> 作者：${escapeHtml(book.author)}
                            </div>
                            <div class="card-meta">
                                <span class="price">¥${escapeHtml(bookPrice)}</span>
                                <span class="book-tag">${bookTag}</span>
                            </div>
                            <div class="book-additional">
                                ${book.stock > 0 ? `<span class="book-stock">库存：${escapeHtml(book.stock)}</span>` : ''}
                            </div>
                            <div class="create-time">
                                <i class="fa fa-clock-o"></i> ${escapeHtml(book.createTime)} · ${escapeHtml(book.seller)}
                            </div>
                            <div class="seller-contact">
                                <i class="fa fa-phone"></i> ${escapeHtml(book.contact)}
                            </div>
                        </div>
                    </div>
                </a>
            </div>
        `;
    });
    
    container.innerHTML = html;
    
    // 初始化滚动动画
    setTimeout(() => {
        initScrollAnimations();
    }, 100);
}

// 渲染分页
function renderPagination() {
    const pagination = document.getElementById('pagination');
    const totalPages = Math.ceil(filteredBooks.length / booksPerPage);
    
    // 清空现有分页
    pagination.innerHTML = '';
    
    // 添加首页按钮
    addPageButton(1, '首页');
    
    // 添加上一页按钮
    addPageButton(currentPage - 1, '<i class="fa fa-angle-left"></i>', currentPage > 1);
    
    // 添加页码按钮（显示当前页前后2页）
    for (let i = Math.max(1, currentPage - 2); i <= Math.min(totalPages, currentPage + 2); i++) {
        addPageButton(i, i, true, i === currentPage);
    }
    
    // 添加下一页按钮
    addPageButton(currentPage + 1, '<i class="fa fa-angle-right"></i>', currentPage < totalPages);
    
    // 添加末页按钮
    addPageButton(totalPages, '末页');
}

// 添加分页按钮
function addPageButton(pageNum, text, isEnabled = true, isActive = false) {
    const pagination = document.getElementById('pagination');
    const li = document.createElement('li');
    li.className = 'page-item';
    
    const a = document.createElement('a');
    a.className = `page-link ${isActive ? 'active' : ''}`;
    a.innerHTML = text;
    
    if (isEnabled) {
        a.addEventListener('click', function(e) {
            e.preventDefault();
            currentPage = pageNum;
            renderBooks();
            renderPagination();
            window.scrollTo({ top: 300, behavior: 'smooth' });
        });
    } else {
        a.style.opacity = '0.5';
        a.style.pointerEvents = 'none';
    }
    
    li.appendChild(a);
    pagination.appendChild(li);
}

// 更新用户菜单状态
function updateUserMenu() {
    const user = getCurrentUser(); // 使用 common.js 中的标准函数
    const userMenu = document.getElementById('userMenu');
    if (user) {
        userMenu.innerHTML = `               <a class="nav-link dropdown-toggle" href="#" role="button" data-bs-toggle="dropdown">
                   <i class="fa fa-user text-primary"></i> ${user.user?.username || user.username || '用户'}               </a>
               <ul class="dropdown-menu dropdown-menu-end">
                   <li><a class="dropdown-item" href="/personalCenter">个人中心</a></li>
                   <li><a class="dropdown-item" href="/myBooks">我的书籍</a></li>
                   <li><a class="dropdown-item" href="/myCollections">我的收藏</a></li>
                   <li><hr class="dropdown-divider"></li>
                   <li><a class="dropdown-item" href="javascript:logout()">退出登录</a></li>
               </ul>
           `;
    } else {
        userMenu.innerHTML = `               <a class="nav-link dropdown-toggle" href="#" role="button" data-bs-toggle="dropdown">
                   <i class="fa fa-user text-primary"></i> 登录/注册
               </a>
               <ul class="dropdown-menu dropdown-menu-end">
                   <li><a class="dropdown-item" href="/login">登录</a></li>
                   <li><a class="dropdown-item" href="/register">注册</a></li>
               </ul>
           `;
    }
}

// 从localStorage获取当前用户
// 改进的 getCurrentUser 函数
function getCurrentUser() {
    try {
        const userStr = localStorage.getItem('currentUser');
        return userStr ? JSON.parse(userStr) : null;
    } catch (e) {
        console.error('解析用户信息失败:', e);
        return null;
    }
}

// 退出登录
function logout() {
    localStorage.removeItem('currentUser');
    window.dispatchEvent(new Event('storage'));
    window.location.href = '/login';
}