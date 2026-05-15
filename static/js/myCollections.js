// 页面加载时检查登录状态
document.addEventListener('DOMContentLoaded', function() {
    // 确保common.js已加载
    if (typeof checkLogin !== 'function') {
        console.error('checkLogin函数未定义，请确保common.js已加载');
        return;
    }
    
    // 检查登录状态
    if (!checkLogin('/myCollections')) {
        return;
    }
    
    // 更新用户名显示
    if (typeof getCurrentUser === 'function') {
        const user = getCurrentUser();
        const usernameElement = document.getElementById('username');
        if (usernameElement && user) {
            usernameElement.textContent = user.username || user.user?.username || '我的账户';
        }
    }
    
    // 更新用户菜单
    if (typeof updateUserMenu === 'function') {
        updateUserMenu();
    }
    
    // 加载我的收藏
    loadCollections();
    
    // 监听storage事件，实时更新收藏列表
    window.addEventListener('storage', function() {
        loadCollections();
    });
    
    // 退出登录事件
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', function(e) {
            e.preventDefault();
            if (typeof logout === 'function') {
                logout();
            } else {
                localStorage.removeItem('currentUser');
                window.location.href = '/login';
            }
        });
    }
});

// 加载我的收藏
async function loadCollections() {
    const container = document.getElementById('collectionsContainer');
    if (!container) return;
    
    try {
        // 显示加载状态
        container.innerHTML = '<div class="loading">正在加载收藏...</div>';
        
        // 从API获取收藏数据
        const response = await fetch('/api/collections', {
            credentials: 'include'
        });
        
        if (!response.ok) {
            if (response.status === 401) {
                window.location.href = '/login?redirect=/myCollections';
                return;
            }
            throw new Error('获取收藏数据失败');
        }
        
        const result = await response.json();
        
        if (result.status === 'success') {
            const collectedBooks = result.collections || result.books || [];
            
            // 数据字段映射和标准化
            const books = collectedBooks.map(book => ({
                id: book.id || '',
                title: book.title || '未知书名',
                category: book.category || '',
                price: parseFloat(book.price || 0),
                createTime: book.created_at || book.createTime || book.publish_date || '',
                imgs: (() => {
                    if (book.cover_url) return [book.cover_url];
                    if (Array.isArray(book.imgs) && book.imgs.length > 0) return book.imgs;
                    if (book.image) return [book.image];
                    return ['https://picsum.photos/id/24/300/400'];
                })(),
                seller: book.owner_name || book.seller || '匿名用户'
            }));
            
            if (books.length === 0) {
                container.innerHTML = `
                    <div class="empty-state">
                        <i class="fa fa-star-o"></i>
                        <h3>您还没有收藏任何书籍</h3>
                        <p>在书籍详情页点击收藏按钮将书籍添加到这里</p>
                    </div>
                `;
                return;
            }
            
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
            
            let html = '';
            books.forEach(book => {
                html += `
                    <div class="collection-card">
                        <div class="book-cover">
                            <img src="${escapeHtml(book.imgs[0])}" alt="${escapeHtml(book.title)}" loading="lazy">
                            <div class="remove-collection" onclick="removeCollection('${book.id}')"><i class="fa fa-times"></i></div>
                        </div>
                        <div class="book-info">
                            <div class="book-title">${escapeHtml(book.title)}</div>
                            <div class="book-meta">
                                <span>${escapeHtml(getCategoryName(book.category))}</span> · 发布于 ${escapeHtml(book.createTime)}
                            </div>
                            <div class="book-price">￥${escapeHtml(book.price.toFixed(2))}</div>
                            <div class="book-seller">
                                <i class="fa fa-user"></i> 卖家: ${escapeHtml(book.seller)}
                            </div>
                            <button class="btn-contact" onclick="viewBookDetail('${book.id}')">查看详情</button>
                        </div>
                    </div>
                `;
            });
            
            container.innerHTML = html;
        } else {
            container.innerHTML = `
                <div class="empty-state">
                    <h3>加载失败，请刷新重试</h3>
                </div>
            `;
        }
    } catch (error) {
        console.error('加载收藏失败:', error);
        container.innerHTML = `
            <div class="empty-state">
                <h3>加载失败，请刷新重试</h3>
            </div>
        `;
    }
}

// 移除收藏
async function removeCollection(bookId) {
    if (!confirm('确定要取消收藏这本书吗？')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/collections/${bookId}`, {
            method: 'POST',
            credentials: 'include'
        });
        
        const result = await response.json();
        
        if (result.status === 'success') {
            alert('已取消收藏');
            await loadCollections(); // 重新加载收藏列表
        } else {
            alert('取消收藏失败：' + (result.message || '未知错误'));
        }
    } catch (error) {
        console.error('取消收藏失败:', error);
        alert('取消收藏时发生错误，请稍后重试');
    }
}

// 查看书籍详情
function viewBookDetail(bookId) {
    window.location.href = `/book1?id=${bookId}`;
}

// 获取分类名称
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