// 页面加载时检查登录状态
document.addEventListener('DOMContentLoaded', function() {
    // 确保common.js已加载
    if (typeof checkLogin !== 'function') {
        console.error('checkLogin函数未定义，请确保common.js已加载');
        return;
    }
    
    // 检查登录状态
    if (!checkLogin('/myBooks')) {
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
    
    // 加载我的书籍
    loadMyBooks();
    
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

// 加载我的书籍
async function loadMyBooks() {
    const container = document.getElementById('myBooksContainer');
    if (!container) return;
    
    const user = getCurrentUser();
    if (!user) {
        container.innerHTML = '<div class="empty-state"><h3>请先登录</h3></div>';
        return;
    }
    
    try {
        // 显示加载状态
        container.innerHTML = '<div class="loading">正在加载...</div>';
        
        // 从API获取书籍数据
        const response = await fetch('/api/books?page_size=1000', {
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
                price: parseFloat(book.price || 0),
                createTime: book.created_at || book.createTime || book.publish_date || '',
                status: book.status || 'available',
                imgs: (() => {
                    if (book.cover_url) return [book.cover_url];
                    if (Array.isArray(book.imgs) && book.imgs.length > 0) return book.imgs;
                    if (book.image) return [book.image];
                    return ['https://picsum.photos/id/24/300/400'];
                })()
            }));
            
            if (userBooks.length === 0) {
                container.innerHTML = `
                    <div class="empty-state">
                        <i class="fa fa-book"></i>
                        <h3>您还没有发布任何书籍</h3>
                        <p>点击"发布新书籍"按钮开始您的书籍交易之旅</p>
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
            userBooks.forEach(book => {
                // 根据状态设置按钮文本（使用common.js中的函数）
                const statusBtnText = book.status === 'available' ? '标记为已售出' : '标记为在售';
                const statusText = typeof getStatusText === 'function' ? getStatusText(book.status) : (book.status === 'available' ? '在售' : '已售出');
                
                html += `
                    <div class="book-card">
                        <div class="book-cover">
                            <img src="${escapeHtml(book.imgs[0])}" alt="${escapeHtml(book.title)}" loading="lazy">
                        </div>
                        <div class="book-info">
                            <div class="book-title">${escapeHtml(book.title)}</div>
                            <div class="book-meta">
                                <span>${escapeHtml(getCategoryName(book.category))}</span> · 发布于 ${escapeHtml(book.createTime)}
                            </div>
                            <div class="book-price">￥${escapeHtml(book.price.toFixed(2))}</div>
                            <div>
                                <span class="book-status status-${book.status}">${statusText}</span>
                            </div>
                            <div class="book-actions">
                                <!-- 状态切换按钮 -->
                                <button class="btn-action btn-status" onclick="toggleBookStatus('${book.id}')">${statusBtnText}</button>
                                <button class="btn-action btn-edit" onclick="editBook('${book.id}')">编辑</button>
                                <button class="btn-action btn-delete" onclick="deleteBook('${book.id}')">删除</button>
                            </div>
                        </div>
                    </div>
                `;
            });
            
            container.innerHTML = html;
        } else {
            container.innerHTML = '<div class="empty-state"><h3>加载失败，请刷新重试</h3></div>';
        }
    } catch (error) {
        console.error('加载我的书籍失败:', error);
        container.innerHTML = '<div class="empty-state"><h3>加载失败，请刷新重试</h3></div>';
    }
}

// 编辑书籍
function editBook(bookId) {
    // 跳转到发布页面并携带书籍ID
    window.location.href = `/publishBook?edit=${bookId}`;
}

// 删除书籍
async function deleteBook(bookId) {
    if (!confirm('确定要删除这本书吗？此操作不可撤销。')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/books/${bookId}`, {
            method: 'DELETE',
            credentials: 'include'
        });
        
        const result = await response.json();
        
        if (result.status === 'success') {
            alert('书籍已删除');
            await loadMyBooks(); // 重新加载书籍列表
        } else {
            alert('删除失败：' + (result.message || '未知错误'));
        }
    } catch (error) {
        console.error('删除书籍失败:', error);
        alert('删除书籍时发生错误，请稍后重试');
    }
}

// 切换书籍状态（可售/已售出）
async function toggleBookStatus(bookId) {
    try {
        // 先获取当前书籍信息
        const response = await fetch(`/api/books/${bookId}`, {
            credentials: 'include'
        });
        
        if (!response.ok) {
            throw new Error('获取书籍信息失败');
        }
        
        const result = await response.json();
        
        if (result.status === 'success' && result.book) {
            const book = result.book;
            const currentStatus = book.status || 'available';
            const newStatus = currentStatus === 'available' ? 'sold' : 'available';
            const statusText = newStatus === 'available' ? '可售' : '已售出';
            
            // 更新状态
            const updateResponse = await fetch(`/api/books/${bookId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                credentials: 'include',
                body: JSON.stringify({
                    status: newStatus
                })
            });
            
            const updateResult = await updateResponse.json();
            
            if (updateResult.status === 'success') {
                alert(`书籍已更新为${statusText}状态`);
                await loadMyBooks(); // 重新加载书籍列表
            } else {
                alert('更新状态失败：' + (updateResult.message || '未知错误'));
            }
        } else {
            alert('获取书籍信息失败');
        }
    } catch (error) {
        console.error('切换书籍状态失败:', error);
        alert('更新状态时发生错误，请稍后重试');
    }
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