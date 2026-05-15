/**
 * 评论功能 JavaScript
 */

// 全局变量
// 注意：currentBookId 在 book1.js 中已经声明，这里不再重复声明
let comments = [];

/**
 * 获取书籍ID（从全局变量或URL参数）
 */
function getBookId() {
    // 尝试从全局变量获取（book1.js 中声明的）
    // 由于 currentBookId 在 book1.js 中是用 let 声明的，在全局作用域中
    // 我们需要通过 window 对象或直接访问
    try {
        if (typeof window.currentBookId !== 'undefined' && window.currentBookId) {
            return window.currentBookId;
        }
    } catch (e) {
        // 忽略
    }
    
    // 从URL参数获取
    const urlParams = new URLSearchParams(window.location.search);
    const idFromUrl = urlParams.get('id');
    if (idFromUrl) {
        return idFromUrl;
    }
    
    return null;
}

// 确保 getCurrentUser 函数可用（如果 common.js 已加载）
if (typeof getCurrentUser === 'undefined') {
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
}

/**
 * 初始化评论功能
 */
async function initComments(bookId) {
    if (!bookId) {
        console.error('评论功能初始化失败：书籍ID为空');
        return;
    }
    
    // 将书籍ID存储到全局变量（通过 window 对象，避免变量冲突）
    window.currentBookId = bookId;
    
    console.log('初始化评论功能，书籍ID:', bookId);
    
    // 检查登录状态，更新评论表单显示
    const isLoggedIn = await checkLoginStatus();
    
    // 加载评论列表
    await loadComments();
    
    // 绑定事件（只有在已登录时才绑定，确保表单存在）
    if (isLoggedIn) {
        // 延迟绑定，确保DOM已更新
        setTimeout(() => {
            bindCommentEvents();
        }, 100);
    }
}

/**
 * 检查登录状态并更新评论表单显示
 */
async function checkLoginStatus() {
    const commentFormContainer = document.getElementById('commentFormContainer');
    if (!commentFormContainer) {
        console.warn('评论表单容器不存在');
        return false;
    }
    
    try {
        // 先从服务器检查登录状态
        const response = await fetch('/api/user/info', {
            credentials: 'include'
        });
        
        if (!response.ok || response.status === 401) {
            // 未登录，显示登录提示
            const hasForm = commentFormContainer.querySelector('.form-group');
            if (hasForm) {
                // 只有当确实存在表单时才替换
                commentFormContainer.innerHTML = `
                    <div class="comment-login-prompt">
                        <p>
                            请先 <a href="/login?redirect=${encodeURIComponent(window.location.href)}">登录</a> 后发表评论
                        </p>
                    </div>
                `;
            } else if (!commentFormContainer.querySelector('.comment-login-prompt')) {
                // 如果既没有表单也没有登录提示，添加登录提示
                commentFormContainer.innerHTML = `
                    <div class="comment-login-prompt">
                        <p>
                            请先 <a href="/login?redirect=${encodeURIComponent(window.location.href)}">登录</a> 后发表评论
                        </p>
                    </div>
                `;
            }
            return false;
        }
        
        // 已登录，确保评论表单显示
        const data = await response.json();
        if (data.status === 'success' && data.user) {
            // 保存用户信息到本地存储
            try {
                if (typeof saveUser === 'function') {
                    saveUser(data.user);
                } else {
                    localStorage.setItem('currentUser', JSON.stringify(data.user));
                }
            } catch (e) {
                console.warn('保存用户信息失败:', e);
            }
        }
        
        // 如果表单被替换成了登录提示，需要恢复表单
        if (!commentFormContainer.querySelector('.form-group')) {
            commentFormContainer.innerHTML = `
                <div class="form-group">
                    <textarea
                        id="commentInput"
                        class="form-control"
                        rows="4"
                        placeholder="写下你的评论..."
                    ></textarea>
                </div>
                <div class="form-actions">
                    <button id="submitCommentBtn" class="btn btn-success">
                        <i class="fa fa-paper-plane"></i> 发表评论
                    </button>
                </div>
            `;
        }
        
        return true;
    } catch (error) {
        console.error('检查登录状态失败:', error);
        // 回退到本地检查
        const user = getCurrentUser();
        if (!user) {
            if (commentFormContainer.querySelector('.form-group')) {
                commentFormContainer.innerHTML = `
                    <div class="comment-login-prompt">
                        <p>
                            请先 <a href="/login?redirect=${encodeURIComponent(window.location.href)}">登录</a> 后发表评论
                        </p>
                    </div>
                `;
            }
            return false;
        }
        return true;
    }
}

/**
 * 加载评论列表
 */
async function loadComments() {
    try {
        const bookId = getBookId();
        if (!bookId) {
            console.error('无法获取书籍ID');
            return;
        }
        
        const response = await fetch(`/api/comments/${bookId}`, {
            credentials: 'include'
        });
        
        if (!response.ok) {
            throw new Error('加载评论失败');
        }
        
        const data = await response.json();
        if (data.status === 'success') {
            comments = data.comments.filter(c => !c.is_deleted);
            renderComments();
        }
    } catch (error) {
        console.error('加载评论失败:', error);
        document.getElementById('commentsList').innerHTML = 
            '<div class="text-center text-muted py-4">加载评论失败，请刷新重试</div>';
    }
}

/**
 * 渲染评论列表
 */
function renderComments() {
    const container = document.getElementById('commentsList');
    if (!container) return;
    
    if (comments.length === 0) {
        container.innerHTML = `
            <div class="no-comments text-center py-5">
                <i class="fa fa-comment-o" style="font-size: 3rem; color: #ddd; margin-bottom: 1rem;"></i>
                <p class="text-muted">暂无评论，快来发表第一条评论吧！</p>
            </div>
        `;
        return;
    }
    
    // 获取当前用户信息以判断删除权限
    const currentUser = getCurrentUser();
    
    const html = comments.map(comment => {
        const canDelete = currentUser && (
            (currentUser.id && currentUser.id.toString() === comment.user_id.toString()) ||
            currentUser.is_admin
        );
        
        return `
        <div class="comment-item" data-comment-id="${comment.id}">
            <div class="comment-avatar">
                <i class="fa fa-user-circle"></i>
            </div>
            <div class="comment-content">
                <div class="comment-header-info">
                    <strong class="comment-author">${escapeHtml(comment.username)}</strong>
                    <span class="comment-time">${formatTime(comment.created_at)}</span>
                </div>
                <div class="comment-text">${escapeHtml(comment.content)}</div>
                ${canDelete ? `
                    <div class="comment-actions">
                        <button class="btn btn-sm btn-link text-danger delete-comment-btn" 
                                data-comment-id="${comment.id}">
                            <i class="fa fa-trash"></i> 删除
                        </button>
                    </div>
                ` : ''}
            </div>
        </div>
    `;
    }).join('');
    
    container.innerHTML = html;
    
    // 绑定删除按钮事件
    container.querySelectorAll('.delete-comment-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const commentId = this.getAttribute('data-comment-id');
            deleteComment(commentId);
        });
    });
    
    // 更新评论数量
    updateCommentCount();
}

// 标记事件是否已绑定
let eventsBound = false;

/**
 * 绑定评论相关事件
 */
function bindCommentEvents() {
    console.log('绑定评论事件');
    
    // 如果已绑定过，先移除（通过标记避免重复绑定）
    if (eventsBound) {
        console.log('事件已绑定，跳过');
        return;
    }
    
    // 获取当前元素
    const submitBtn = document.getElementById('submitCommentBtn');
    const commentInput = document.getElementById('commentInput');
    
    if (!submitBtn) {
        console.warn('提交按钮不存在，可能未登录或表单未加载');
        return;
    }
    
    if (!commentInput) {
        console.warn('评论输入框不存在');
        return;
    }
    
    // 绑定提交按钮点击事件
    submitBtn.addEventListener('click', function(e) {
        e.preventDefault();
        e.stopPropagation();
        console.log('点击提交评论按钮');
        submitComment();
    });
    
    // 绑定输入框键盘事件
    commentInput.addEventListener('keydown', function(e) {
        // Ctrl+Enter 或 Cmd+Enter 提交评论
        if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
            e.preventDefault();
            submitComment();
        }
    });
    
    // 绑定删除按钮事件（通过事件委托到整个评论列表容器）
    const commentsList = document.getElementById('commentsList');
    if (commentsList) {
        commentsList.addEventListener('click', function(e) {
            const deleteBtn = e.target.closest('.delete-comment-btn');
            if (deleteBtn) {
                e.preventDefault();
                e.stopPropagation();
                const commentId = deleteBtn.getAttribute('data-comment-id');
                if (commentId) {
                    deleteComment(commentId);
                }
            }
        });
    }
    
    eventsBound = true;
    console.log('评论事件绑定完成');
}

/**
 * 提交评论
 */
async function submitComment() {
    const bookId = getBookId();
    if (!bookId) {
        console.error('无法获取书籍ID');
        alert('书籍信息错误，请刷新页面重试');
        return;
    }
    
    console.log('开始提交评论，书籍ID:', bookId);
    
    const commentInput = document.getElementById('commentInput');
    const submitBtn = document.getElementById('submitCommentBtn');
    
    if (!commentInput) {
        console.error('评论输入框不存在');
        alert('评论输入框不存在，请刷新页面重试');
        return;
    }
    
    if (!submitBtn) {
        console.error('提交按钮不存在');
        alert('提交按钮不存在，请刷新页面重试');
        return;
    }
    
    const content = commentInput.value.trim();
    
    if (!content) {
        alert('请输入评论内容');
        commentInput.focus();
        return;
    }
    
    if (content.length > 1000) {
        alert('评论内容不能超过1000字');
        return;
    }
    
    // 检查是否登录
    try {
        const authResponse = await fetch('/api/user/info', {
            credentials: 'include'
        });
        
        if (!authResponse.ok || authResponse.status === 401) {
            alert('请先登录后再发表评论');
            window.location.href = `/login?redirect=${encodeURIComponent(window.location.href)}`;
            return;
        }
    } catch (error) {
        console.error('检查登录状态失败:', error);
        alert('请先登录后再发表评论');
        window.location.href = `/login?redirect=${encodeURIComponent(window.location.href)}`;
        return;
    }
    
    // 禁用提交按钮
    submitBtn.disabled = true;
    const originalBtnText = submitBtn.innerHTML;
    submitBtn.innerHTML = '<i class="fa fa-spinner fa-spin"></i> 提交中...';
    
    try {
        console.log('发送评论请求:', {
            book_id: bookId,
            content_length: content.length
        });
        
        const response = await fetch('/api/comments', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            credentials: 'include',
            body: JSON.stringify({
                book_id: bookId,
                content: content
            })
        });
        
        console.log('评论API响应状态:', response.status);
        
        let data;
        try {
            data = await response.json();
        } catch (e) {
            const text = await response.text();
            console.error('解析响应失败:', text);
            throw new Error('服务器响应格式错误');
        }
        
        console.log('评论API响应数据:', data);
        
        if (data.status === 'success') {
            commentInput.value = '';
            // 重新加载评论列表
            await loadComments();
            // 提示成功
            const successMsg = document.createElement('div');
            successMsg.className = 'alert alert-success alert-dismissible fade show';
            successMsg.style.position = 'fixed';
            successMsg.style.top = '20px';
            successMsg.style.right = '20px';
            successMsg.style.zIndex = '9999';
            successMsg.innerHTML = `
                <strong>成功！</strong> 评论发表成功
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            `;
            document.body.appendChild(successMsg);
            setTimeout(() => {
                successMsg.remove();
            }, 3000);
        } else {
            alert(data.message || '评论发表失败，请重试');
        }
    } catch (error) {
        console.error('提交评论失败:', error);
        alert('评论发表失败：' + (error.message || '网络错误，请检查网络连接后重试'));
    } finally {
        submitBtn.disabled = false;
        submitBtn.innerHTML = originalBtnText;
    }
}

/**
 * 删除评论
 */
async function deleteComment(commentId) {
    if (!confirm('确定要删除这条评论吗？')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/comments/${commentId}`, {
            method: 'DELETE',
            credentials: 'include'
        });
        
        const data = await response.json();
        
        if (data.status === 'success') {
            await loadComments();
        } else {
            alert(data.message || '删除评论失败，请重试');
        }
    } catch (error) {
        console.error('删除评论失败:', error);
        alert('删除评论失败，请刷新重试');
    }
}

/**
 * 检查是否可以删除评论
 */
async function canDeleteComment(comment) {
    try {
        const user = getCurrentUser();
        if (!user) return false;
        
        // 检查是否是评论作者
        if (user.id && user.id.toString() === comment.user_id.toString()) {
            return true;
        }
        
        // 检查是否是管理员
        if (user.is_admin) {
            return true;
        }
        
        return false;
    } catch (error) {
        console.error('检查删除权限失败:', error);
        return false;
    }
}

/**
 * 更新评论数量
 */
function updateCommentCount() {
    const countElement = document.getElementById('commentCount');
    if (countElement) {
        countElement.textContent = `(${comments.length})`;
    }
}

/**
 * 格式化时间
 */
function formatTime(timeStr) {
    if (!timeStr) return '';
    
    const time = new Date(timeStr.replace(/-/g, '/'));
    const now = new Date();
    const diff = now - time;
    
    const seconds = Math.floor(diff / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);
    
    if (days > 7) {
        return timeStr.split(' ')[0];
    } else if (days > 0) {
        return `${days}天前`;
    } else if (hours > 0) {
        return `${hours}小时前`;
    } else if (minutes > 0) {
        return `${minutes}分钟前`;
    } else {
        return '刚刚';
    }
}

/**
 * HTML 转义
 */
function escapeHtml(unsafe) {
    if (!unsafe) return '';
    return String(unsafe)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

