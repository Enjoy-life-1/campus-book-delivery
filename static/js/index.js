// index.js - 首页功能实现
// 使用common.js中定义的apiRequest函数代替import语句

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

/**
 * 渲染热门书籍列表 - 从API获取数据，显示前6本书
 */
async function renderHotBooks() {
    const container = document.getElementById('hotBooksContainer');
    if (!container) {
        console.warn('热门书籍容器不存在');
        return;
    }
    
    try {
        // 从API获取书籍数据
        const params = new URLSearchParams();
        params.set('page_size', '1000'); // 获取足够多的书籍
        params.set('_t', new Date().getTime()); // 防止缓存
        
        const response = await fetch(`/api/books?${params.toString()}`, {
            credentials: 'include'
        });
        
        if (!response.ok) {
            throw new Error('网络响应失败');
        }
        
        const data = await response.json();
        
        if (data.status === 'success') {
            const booksFromAPI = data.books || [];
            
            // 数据字段映射和标准化
            let allBooks = booksFromAPI.map(book => ({
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
                status: book.status || 'available'
            }));
            
            // 只显示在售的书籍
            allBooks = allBooks.filter(book => book.status === 'available');
            
            // 取前6本书
            const hotBooks = allBooks.slice(0, 6);
            
            if (hotBooks.length === 0) {
                container.innerHTML = '<div class="col-12 text-center text-muted"><p>暂无热门书籍</p></div>';
                return;
            }
            
            // 渲染书籍卡片
            let html = '';
            hotBooks.forEach(book => {
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
        } else {
            console.error('获取热门书籍失败:', data.message);
            container.innerHTML = '<div class="col-12 text-center text-muted"><p>加载失败，请稍后重试</p></div>';
        }
    } catch (error) {
        console.error('获取热门书籍出错:', error);
        const container = document.getElementById('hotBooksContainer');
        if (container) {
            container.innerHTML = '<div class="col-12 text-center text-muted"><p>网络错误，请检查您的网络连接</p></div>';
        }
    }
}

/**
 * 初始化认证功能
 */
async function initAuth() {
    // 暂时禁用API调用，避免错误影响页面功能
    // 后续可以根据实际API路径重新启用
    console.log('认证功能初始化: 跳过API调用');
    return;
    
    /*
    try {
        // 尝试其他可能的认证API路径
        const response = await apiRequest('/api/user/status', {
            method: 'GET'
        });
        
        // 这里可以根据需要处理认证状态
        if (response.logged_in) {
            console.log('用户已登录:', response.user);
            // 更新UI显示用户已登录
        } else {
            console.log('用户未登录');
        }
    } catch (error) {
        console.error('获取认证状态失败:', error);
        // 静默失败，不影响页面其他功能
    }
    */
}

/**
 * 初始化首页功能
 */
async function initHomePage() {
    try {
        // 更新用户菜单（如果common.js中已定义）
        if (typeof updateUserMenu === 'function') {
            updateUserMenu();
        }
        
        // 初始化认证功能
        initAuth();
        
        // 初始化滚动动画
        setTimeout(() => {
            initScrollAnimations();
        }, 500);
        
        // 渲染热门书籍 - 从API获取数据，显示前6本
        await renderHotBooks();
        
        // 初始化分类筛选功能
        initCategoryFilters();
        
        // 初始化搜索功能
        initSearch();
        
    } catch (error) {
        console.error('首页初始化失败:', error);
    }
}

/**
 * 初始化分类筛选功能
 */
function initCategoryFilters() {
    const categoryLinks = document.querySelectorAll('.category-card a, .dropdown-menu .dropdown-item');
    
    categoryLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            // 已经是正确的链接格式，不需要特殊处理
        });
    });
}

/**
 * 初始化搜索功能
 */
function initSearch() {
    const searchBtn = document.getElementById('searchBtn');
    const searchInput = document.getElementById('searchInput');
    
    // 点击搜索按钮
    if (searchBtn) {
        searchBtn.addEventListener('click', function(e) {
            e.preventDefault();
            const keyword = searchInput ? searchInput.value.trim() : '';
            
            if (keyword) {
                window.location.href = `/booksList?keyword=${encodeURIComponent(keyword)}`;
            } else {
                window.location.href = '/booksList';
            }
        });
    }
    
    // 按Enter键搜索
    if (searchInput) {
        searchInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                const keyword = searchInput.value.trim();
                
                if (keyword) {
                    window.location.href = `/booksList?keyword=${encodeURIComponent(keyword)}`;
                } else {
                    window.location.href = '/booksList';
                }
            }
        });
    }
}

/**
 * 滚动动画观察器
 */
function initScrollAnimations() {
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    
    const observer = new IntersectionObserver(function(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);
    
    // 观察所有需要动画的元素
    const animatedElements = document.querySelectorAll('.category-card, .book-card, .feature-tag-enhanced');
    animatedElements.forEach((el, index) => {
        el.style.opacity = '0';
        el.style.transform = 'translateY(30px)';
        el.style.transition = `opacity 0.6s ease ${index * 0.1}s, transform 0.6s ease ${index * 0.1}s`;
        observer.observe(el);
    });
}

/**
 * 页面加载完成后初始化
 */
document.addEventListener('DOMContentLoaded', function() {
    // 仅在首页执行初始化
    if (window.location.pathname === '/') {
        initHomePage();
    }
});

// 为了兼容性，不使用export语句