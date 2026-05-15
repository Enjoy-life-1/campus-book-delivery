// 1. 页面加载时检查登录状态
document.addEventListener('DOMContentLoaded', function() {
    // 确保common.js已加载
    if (typeof checkLogin !== 'function') {
        console.error('checkLogin函数未定义，请确保common.js已加载');
        return;
    }
    
    // 检查登录状态
    if (!checkLogin('/personalCenter')) {
        return;
    }
    
    // 加载用户信息
    loadUserInfo();
    
    // 加载最近发布的书籍
    loadRecentBooks();

    // 监听storage事件更新数据
    window.addEventListener('storage', function(e) {
        // 如果是头像更新事件，刷新头像
        if (e.key === 'avatarUpdated' || !e.key) {
            loadUserInfo();
        }
        loadRecentBooks();
    });
    
    // 监听自定义事件，当头像更新时刷新显示
    window.addEventListener('avatarUpdated', function(e) {
        if (e.detail && e.detail.avatarUrl) {
            updateAvatar(e.detail.avatarUrl);
        } else {
            loadUserInfo();
        }
    });
    
    // 页面可见时刷新头像（从其他页面返回时）
    document.addEventListener('visibilitychange', function() {
        if (!document.hidden) {
            loadUserInfo();
        }
    });
});

// 2. 加载用户信息
async function loadUserInfo() {
    // 确保函数已定义
    if (typeof getCurrentUser !== 'function') {
        console.error('getCurrentUser函数未定义');
        return;
    }
    
    const user = getCurrentUser();
    if (!user) return;
    
    // 更新用户名
    const userNameEl = document.getElementById('userName');
    if (userNameEl) {
        userNameEl.textContent = user.username || user.user?.username || '用户';
    }
    
    // 更新头像 - 优先从API获取最新头像
    let avatarUrl = null;
    try {
        const response = await fetch('/api/user/info', {
            credentials: 'include'
        });
        
        if (response.ok) {
            const result = await response.json();
            if (result.status === 'success' && result.user) {
                const userInfo = result.user;
                avatarUrl = userInfo.avatar || null;
                
                // 更新本地用户信息
                if (userInfo.avatar) {
                    user.avatar = userInfo.avatar;
                }
                if (typeof saveUser === 'function') {
                    saveUser(user);
                }
            }
        }
    } catch (error) {
        console.error('获取用户头像失败:', error);
        // 如果API失败，使用本地存储的头像
        avatarUrl = user.avatar || user.user?.avatar || null;
    }
    
    // 如果仍然没有头像，使用本地存储的头像作为后备
    if (!avatarUrl) {
        avatarUrl = user.avatar || user.user?.avatar || null;
    }
    
    // 更新头像显示
    updateAvatar(avatarUrl);
    
    // 从API获取用户发布的书籍
    try {
        const response = await fetch('/api/books', {
            credentials: 'include'
        });
        
        if (response.ok) {
            const result = await response.json();
            if (result.status === 'success') {
                const allBooks = result.books || [];
                const userId = String(user.id || user.user?.id || '');
                
                // 筛选用户发布的书籍
                const userBooks = allBooks.filter(book => {
                    const ownerId = String(book.owner_id || book.sellerId || '');
                    return ownerId === userId;
                });
                
                // 更新发布数量（带动画）
                const publishedCountEl = document.getElementById('publishedCount');
                if (publishedCountEl) {
                    animateValue(publishedCountEl, 0, userBooks.length, 1000);
                }
                
                // 更新已售出数量（带动画）
                const soldCount = userBooks.filter(book => book.status === 'sold').length;
                const soldCountEl = document.getElementById('soldCount');
                if (soldCountEl) {
                    animateValue(soldCountEl, 0, soldCount, 1000);
                }
            }
        }
    } catch (error) {
        console.error('获取用户书籍失败:', error);
    }

    // 更新收藏数量
    await updateCollectionCount();
}

// 更新头像显示
function updateAvatar(avatarUrl) {
    const avatarImg = document.getElementById('userAvatar');
    const avatarIcon = document.getElementById('avatarIcon');
    
    if (avatarImg && avatarIcon) {
        if (avatarUrl && avatarUrl.trim() !== '') {
            // 显示图片，隐藏图标
            avatarImg.src = avatarUrl;
            avatarImg.style.display = 'block';
            avatarIcon.style.display = 'none';
        } else {
            // 显示图标，隐藏图片
            avatarImg.style.display = 'none';
            avatarIcon.style.display = 'block';
        }
    }
}

// 3. 更新收藏数量
async function updateCollectionCount() {
    const user = getCurrentUser();
    if (!user) return;
    
    try {
        const response = await fetch('/api/collections', {
            credentials: 'include'
        });
        
        if (response.ok) {
            const result = await response.json();
            if (result.status === 'success') {
                const collections = result.collections || [];
                const collectedCountEl = document.getElementById('collectedCount');
                if (collectedCountEl) {
                    const currentValue = parseInt(collectedCountEl.textContent) || 0;
                    animateValue(collectedCountEl, currentValue, collections.length, 1000);
                }
            }
        }
    } catch (error) {
        console.error('获取收藏数量失败:', error);
        // 降级到localStorage
        const collectionKey = `collections_${user.id}`;
        try {
            const collections = JSON.parse(localStorage.getItem(collectionKey) || '[]');
            const collectedCountEl = document.getElementById('collectedCount');
            if (collectedCountEl) {
                const currentValue = parseInt(collectedCountEl.textContent) || 0;
                animateValue(collectedCountEl, currentValue, collections.length, 1000);
            }
        } catch (e) {
            console.error('从localStorage获取收藏数量失败:', e);
        }
    }
}

// 4. 加载最近发布的书籍
async function loadRecentBooks() {
    const container = document.getElementById('recentBooksContainer');
    if (!container) return;
    
    const user = getCurrentUser();
    if (!user) {
        container.innerHTML = '<p class="text-center text-gray p-4">请先登录</p>';
        return;
    }
    
    try {
        const response = await fetch('/api/books', {
            credentials: 'include'
        });
        
        if (!response.ok) {
            throw new Error('获取书籍数据失败');
        }
        
        const result = await response.json();
        if (result.status === 'success') {
            const allBooks = result.books || [];
            const userId = String(user.id || user.user?.id || '');
            
            // 筛选用户发布的书籍
            let userBooks = allBooks.filter(book => {
                const ownerId = String(book.owner_id || book.sellerId || '');
                return ownerId === userId;
            });
            
            // 数据字段映射和标准化
            userBooks = userBooks.map(book => ({
                id: book.id || '',
                title: book.title || '未知书名',
                category: book.category || '',
                createTime: book.created_at || book.createTime || book.publish_date || '',
                status: book.status || 'available',
                imgs: (() => {
                    if (book.cover_url) return [book.cover_url];
                    if (Array.isArray(book.imgs) && book.imgs.length > 0) return book.imgs;
                    if (book.image) return [book.image];
                    return ['https://picsum.photos/id/48/100/150'];
                })()
            }));
            
            // 按发布时间排序，只显示最近3本
            const recentBooks = [...userBooks].sort((a, b) => {
                const dateA = new Date(a.createTime || 0);
                const dateB = new Date(b.createTime || 0);
                return dateB - dateA;
            }).slice(0, 3);
            
            if (recentBooks.length === 0) {
                container.innerHTML = '<p class="text-center text-gray p-4">您还没有发布任何书籍</p>';
                return;
            }
            
            // 清空容器
            container.innerHTML = '';
            
            // 安全地转义HTML特殊字符
            const escapeHtml = (unsafe) => {
                if (!unsafe) return '';
                return String(unsafe)
                    .replace(/&/g, "&amp;")
                    .replace(/</g, "&lt;")
                    .replace(/>/g, "&gt;")
                    .replace(/"/g, "&quot;")
                    .replace(/'/g, "&#039;");
            };
            
            // 添加书籍项
            recentBooks.forEach(book => {
                const bookItem = document.createElement('div');
                bookItem.className = 'book-item';
                
                // 添加点击事件，跳转到书籍详情页
                bookItem.style.cursor = 'pointer';
                bookItem.addEventListener('click', function() {
                    window.location.href = `/book1?id=${book.id}`;
                });
                
                // 状态类名和文本
                const statusClass = book.status === 'available' ? 'status-available' : 'status-sold';
                const statusText = book.status === 'available' ? '可售' : '已售出';
                
                bookItem.innerHTML = `
                    <div class="book-cover">
                        <img src="${escapeHtml(book.imgs[0])}" alt="${escapeHtml(book.title)}" loading="lazy">
                    </div>
                    <div class="book-details">
                        <div class="book-title">${escapeHtml(book.title)}</div>
                        <div class="book-meta">
                            <span>${escapeHtml(getCategoryName(book.category))}</span> · 发布于 ${escapeHtml(book.createTime)}
                        </div>
                        <span class="book-status ${statusClass}">${statusText}</span>
                    </div>
                `;
                
                container.appendChild(bookItem);
            });
        } else {
            container.innerHTML = '<p class="text-center text-gray p-4">加载失败，请刷新重试</p>';
        }
    } catch (error) {
        console.error('加载最近书籍失败:', error);
        container.innerHTML = '<p class="text-center text-gray p-4">加载失败，请刷新重试</p>';
    }
}

// 辅助函数：获取分类名称
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

// 数字计数动画函数
function animateValue(element, start, end, duration) {
    if (start === end) {
        element.textContent = end;
        return;
    }
    
    const range = end - start;
    const increment = end > start ? 1 : -1;
    const stepTime = Math.abs(Math.floor(duration / range));
    let current = start;
    
    const timer = setInterval(function() {
        current += increment;
        element.textContent = current;
        
        if ((increment > 0 && current >= end) || (increment < 0 && current <= end)) {
            element.textContent = end;
            clearInterval(timer);
        }
    }, stepTime);
}

// 页面加载初始化
window.onload = function() {
    // 确保common.js已加载
    if (typeof updateUserMenu === 'function') {
        updateUserMenu(); // 同步登录状态
    } else {
        console.warn('updateUserMenu函数未定义，请确保common.js已加载');
    }
    
    updateCollectionCount();
    window.addEventListener('storage', updateCollectionCount);
};