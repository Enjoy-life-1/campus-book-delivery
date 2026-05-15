// 页面加载时检查登录状态
document.addEventListener('DOMContentLoaded', function() {
    // 确保common.js已加载
    if (typeof checkLogin !== 'function') {
        console.error('checkLogin函数未定义，请确保common.js已加载');
        return;
    }
    
    // 检查登录状态
    if (!checkLogin('/transactionHistory')) {
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
    
    // 检查URL参数，确定初始过滤条件
    let initialFilter = 'all';
    try {
        const urlParams = new URLSearchParams(window.location.search);
        const typeParam = urlParams.get('type');
        
        // 处理从购买按钮跳转过来的参数
        if (typeParam === 'buy') {
            initialFilter = 'buying';
            
            // 自动激活"我买到的"标签
            setTimeout(() => {
                const buyingTab = document.querySelector('.filter-tab[data-filter="buying"]');
                if (buyingTab) {
                    // 更新活跃状态
                    document.querySelectorAll('.filter-tab').forEach(t => t.classList.remove('active'));
                    buyingTab.classList.add('active');
                }
            }, 100);
        } else if (typeParam === 'sell') {
            initialFilter = 'selling';
        }
    } catch (error) {
        console.warn('处理URL参数失败:', error);
    }
    
    // 加载交易记录
    loadTransactions(initialFilter);
    
    // 过滤标签点击事件
    document.querySelectorAll('.filter-tab').forEach(tab => {
        tab.addEventListener('click', function() {
            // 更新活跃状态
            document.querySelectorAll('.filter-tab').forEach(t => t.classList.remove('active'));
            this.classList.add('active');
            
            // 加载对应交易记录
            const filter = this.dataset.filter;
            loadTransactions(filter);
        });
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

// 加载交易记录
async function loadTransactions(filter = 'all') {
    const container = document.getElementById('transactionsContainer');
    if (!container) return;
    
    try {
        // 显示加载状态
        container.innerHTML = '<div class="loading">正在加载交易记录...</div>';
        
        // 从API获取订单数据
        const response = await fetch('/api/orders', {
            credentials: 'include'
        });
        
        if (!response.ok) {
            if (response.status === 401) {
                window.location.href = '/login?redirect=/transactionHistory';
                return;
            }
            throw new Error('获取交易数据失败');
        }
        
        const result = await response.json();
        
        if (result.status === 'success') {
            const orders = result.orders || [];
            
            // 获取书籍数据以补充订单信息（包括已售出的书籍）
            const booksParams = new URLSearchParams();
            booksParams.set('include_sold', 'true');  // 包含已售出的书籍
            booksParams.set('page_size', '10000');  // 获取足够多的书籍
            
            const booksResponse = await fetch(`/api/books?${booksParams.toString()}`, {
                credentials: 'include'
            });
            let books = [];
            if (booksResponse.ok) {
                const booksResult = await booksResponse.json();
                books = booksResult.books || [];
            }
            
            // 处理交易数据
            const transactions = processTransactions(orders, books, filter);
            
            if (transactions.length === 0) {
                container.innerHTML = `
                    <div class="empty-state">
                        <i class="fa fa-filter"></i>
                        <h3>没有符合条件的交易记录</h3>
                        <p>尝试调整筛选条件或清除所有筛选</p>
                    </div>
                `;
                return;
            }
            
            // 按日期排序（新的在前）
            transactions.sort((a, b) => {
                return new Date(b.date) - new Date(a.date);
            });
            
            // 渲染交易记录
            renderTransactions(transactions, container);
        } else {
            container.innerHTML = `
                <div class="empty-state">
                    <h3>加载失败，请刷新重试</h3>
                </div>
            `;
        }
    } catch (error) {
        console.error('加载交易记录失败:', error);
        container.innerHTML = `
            <div class="empty-state">
                <h3>加载失败，请刷新重试</h3>
                <p>${error.message}</p>
            </div>
        `;
    }
}

// 处理交易数据
function processTransactions(orders, books, filter) {
    const user = getCurrentUser();
    if (!user) return [];
    
    const user_id = String(user.id || user.user?.id || '');
    
    // 创建书籍映射（确保ID匹配正确）
    const bookMap = {};
    books.forEach(book => {
        if (book && book.id) {
            // 统一转换为字符串进行映射
            const bookId = String(book.id);
            bookMap[bookId] = book;
        }
    });
    
    // 处理订单数据
    const transactions = [];
    
    orders.forEach(order => {
        const order_buyer_id = String(order.buyer_id || '');
        const order_seller_id = String(order.seller_id || '');
        
        // 判断是买入还是卖出
        let type = '';
        if (order_buyer_id === user_id) {
            type = 'buying';
        } else if (order_seller_id === user_id) {
            type = 'selling';
        } else {
            return; // 跳过不相关的订单
        }
        
        // 根据筛选条件过滤
        if (filter !== 'all' && type !== filter) {
            return;
        }
        
        // 获取书籍信息
        const book_id = String(order.book_id || '');
        const book = bookMap[book_id] || {};
        
        // 获取书籍图片，优先使用书籍信息中的图片
        let bookImage = 'https://picsum.photos/id/24/300/400'; // 默认图片
        if (book && Object.keys(book).length > 0) {
            // 如果找到了书籍信息，使用书籍的图片
            if (book.cover_url) {
                bookImage = book.cover_url;
            } else if (Array.isArray(book.imgs) && book.imgs.length > 0) {
                bookImage = book.imgs[0];
            } else if (book.image) {
                bookImage = book.image;
            }
        }
        
        // 构建交易记录
        const transaction = {
            id: order.id || '',
            type: type,
            bookId: book_id,
            bookTitle: order.book_title || book.title || '未知书名',
            bookImage: bookImage,
            price: parseFloat(order.price || book.price || 0),
            status: order.status || 'pending',
            date: order.created_at || '',
            buyerName: order.buyer_name || '未知买家',
            sellerName: order.seller_name || '未知卖家',
            counterpartName: type === 'buying' ? order.seller_name : order.buyer_name
        };
        
        transactions.push(transaction);
    });
    
    return transactions;
}

// 渲染交易记录
function renderTransactions(transactions, container) {
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
    
    // 获取状态文本和样式
    const getStatusInfo = (status) => {
        const statusMap = {
            'pending': { text: '待处理', class: 'status-pending' },
            'completed': { text: '已完成', class: 'status-completed' },
            'cancelled': { text: '已取消', class: 'status-cancelled' },
            'processing': { text: '处理中', class: 'status-processing' }
        };
        return statusMap[status] || { text: status, class: 'status-unknown' };
    };
    
    let html = '';
    transactions.forEach(transaction => {
        const statusInfo = getStatusInfo(transaction.status);
        const typeText = transaction.type === 'buying' ? '买入' : '卖出';
        const counterpartText = transaction.type === 'buying' ? '卖家' : '买家';
        
        html += `
            <div class="transaction-card">
                <div class="transaction-image">
                    <img src="${escapeHtml(transaction.bookImage)}" alt="${escapeHtml(transaction.bookTitle)}" loading="lazy">
                </div>
                <div class="transaction-info">
                    <div class="transaction-header">
                        <h4 class="transaction-title">${escapeHtml(transaction.bookTitle)}</h4>
                        <span class="transaction-type ${transaction.type}">${typeText}</span>
                    </div>
                    <div class="transaction-details">
                        <div class="detail-item">
                            <span class="detail-label">${counterpartText}:</span>
                            <span class="detail-value">${escapeHtml(transaction.counterpartName)}</span>
                        </div>
                        <div class="detail-item">
                            <span class="detail-label">价格:</span>
                            <span class="detail-value price">￥${escapeHtml(transaction.price.toFixed(2))}</span>
                        </div>
                        <div class="detail-item">
                            <span class="detail-label">日期:</span>
                            <span class="detail-value">${escapeHtml(transaction.date)}</span>
                        </div>
                        <div class="detail-item">
                            <span class="detail-label">状态:</span>
                            <span class="detail-value ${statusInfo.class}">${statusInfo.text}</span>
                        </div>
                    </div>
                    <div class="transaction-actions">
                        <button class="btn-view" onclick="viewBookDetail('${escapeHtml(transaction.bookId)}')">查看书籍</button>
                        <button class="btn-view" onclick="viewOrderDetail('${escapeHtml(transaction.id)}')">订单详情</button>
                    </div>
                </div>
            </div>
        `;
    });
    
    container.innerHTML = html;
}

// 查看书籍详情
function viewBookDetail(bookId) {
    window.location.href = `/book1?id=${bookId}`;
}

// 查看订单详情
function viewOrderDetail(orderId) {
    window.location.href = `/orderDetails?id=${orderId}`;
}
