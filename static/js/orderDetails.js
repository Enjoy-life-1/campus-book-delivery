// 全局变量
let currentOrder = null;
let currentUser = null;
let currentBook = null;
let bookId = null;

// 页面加载时初始化
document.addEventListener('DOMContentLoaded', function() {
    // 检查登录状态
    if (!checkLogin('/orderDetails')) {
        return;
    }
    
    // 获取当前用户
    currentUser = getCurrentUser();
    if (!currentUser) {
        showError('请先登录');
        return;
    }
    
    // 更新用户名显示
    const usernameElement = document.getElementById('username');
    if (usernameElement && currentUser) {
        usernameElement.textContent = currentUser.username || currentUser.user?.username || '我的账户';
    }
    
    // 更新用户菜单
    if (typeof updateUserMenu === 'function') {
        updateUserMenu();
    }
    
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
    
    // 从URL获取订单ID
    const urlParams = new URLSearchParams(window.location.search);
    const orderId = urlParams.get('id');
    
    if (!orderId) {
        // 如果没有订单ID，显示订单列表供用户选择
        loadOrderList();
        return;
    }
    
    // 加载订单详情
    loadOrderDetails(orderId);
    
    // 初始化评价表单
    initReviewForm();
});

// 加载订单详情
async function loadOrderDetails(orderId) {
    const loadingContainer = document.getElementById('loadingContainer');
    const orderContainer = document.getElementById('orderContainer');
    const errorContainer = document.getElementById('errorContainer');
    
    try {
        loadingContainer.style.display = 'block';
        orderContainer.style.display = 'none';
        errorContainer.style.display = 'none';
        
        // 获取订单详情
        const response = await fetch(`/api/orders/${orderId}`, {
            credentials: 'include'
        });
        
        if (!response.ok) {
            if (response.status === 401) {
                window.location.href = '/login?redirect=/orderDetails?id=' + orderId;
                return;
            }
            if (response.status === 404) {
                throw new Error('订单不存在');
            }
            throw new Error('获取订单详情失败');
        }
        
        const result = await response.json();
        
        if (result.status === 'success') {
            currentOrder = result.order;
            bookId = currentOrder.book_id;
            
            // 加载书籍信息
            await loadBookDetails(bookId);
            
            // 渲染订单信息
            renderOrderDetails();
            
            // 检查是否已评价
            await checkReviewStatus();
            
            loadingContainer.style.display = 'none';
            orderContainer.style.display = 'block';
        } else {
            throw new Error(result.message || '获取订单详情失败');
        }
    } catch (error) {
        console.error('加载订单详情失败:', error);
        loadingContainer.style.display = 'none';
        showError(error.message || '加载失败，请刷新重试');
    }
}

// 加载书籍详情
async function loadBookDetails(bookId) {
    try {
        const response = await fetch(`/api/books/${bookId}`, {
            credentials: 'include'
        });
        
        if (response.ok) {
            const result = await response.json();
            if (result.status === 'success') {
                currentBook = result.book;
            }
        }
    } catch (error) {
        console.error('加载书籍详情失败:', error);
    }
}

// 渲染订单详情
function renderOrderDetails() {
    if (!currentOrder) return;
    
    // 订单基本信息
    document.getElementById('orderId').textContent = currentOrder.id;
    document.getElementById('orderDate').textContent = currentOrder.created_at || '';
    
    // 订单状态
    const statusBadge = document.getElementById('statusBadge');
    const status = currentOrder.status || 'pending';
    
    statusBadge.className = 'status-badge ' + status;
    const statusMap = {
        'pending': { text: '待处理', icon: 'fa-clock-o' },
        'shipped': { text: '已发货', icon: 'fa-truck' },
        'completed': { text: '已完成', icon: 'fa-check-circle' },
        'cancelled': { text: '已取消', icon: 'fa-times-circle' }
    };
    const statusInfo = statusMap[status] || statusMap['pending'];
    statusBadge.innerHTML = `<i class="fa ${statusInfo.icon}"></i> <span>${statusInfo.text}</span>`;
    
    // 书籍信息
    document.getElementById('bookTitle').textContent = currentOrder.book_title || '未知书名';
    document.getElementById('bookPrice').textContent = (currentOrder.price || 0).toFixed(2);
    
    // 书籍图片
    let bookImage = 'https://picsum.photos/id/24/300/400';
    if (currentBook) {
        if (currentBook.cover_url) {
            bookImage = currentBook.cover_url;
        } else if (Array.isArray(currentBook.imgs) && currentBook.imgs.length > 0) {
            bookImage = currentBook.imgs[0];
        } else if (currentBook.image) {
            bookImage = currentBook.image;
        }
    }
    document.getElementById('bookImage').src = bookImage;
    
    // 交易双方信息
    document.getElementById('sellerName').textContent = currentOrder.seller_name || '未知卖家';
    document.getElementById('sellerId').textContent = currentOrder.seller_id || '';
    document.getElementById('buyerName').textContent = currentOrder.buyer_name || '未知买家';
    document.getElementById('buyerId').textContent = currentOrder.buyer_id || '';
    
    // 显示操作按钮
    showActionButtons();
}

// 显示操作按钮
function showActionButtons() {
    if (!currentOrder || !currentUser) return;
    
    const userId = String(currentUser.id || currentUser.user?.id || '');
    const sellerId = String(currentOrder.seller_id || '');
    const buyerId = String(currentOrder.buyer_id || '');
    const status = currentOrder.status || 'pending';
    
    const shippedBtn = document.getElementById('shippedBtn');
    const receivedBtn = document.getElementById('receivedBtn');
    const actionButtonsSection = document.getElementById('actionButtonsSection');
    
    // 隐藏所有按钮
    shippedBtn.style.display = 'none';
    receivedBtn.style.display = 'none';
    
    // 卖家可以点击"已发货"
    if (userId === sellerId && status === 'pending') {
        shippedBtn.style.display = 'inline-flex';
        shippedBtn.onclick = () => updateOrderStatus('shipped');
    }
    
    // 买家可以点击"已收货"
    if (userId === buyerId && status === 'shipped') {
        receivedBtn.style.display = 'inline-flex';
        receivedBtn.onclick = () => updateOrderStatus('completed');
    }
    
    // 如果订单已完成，显示评价区域
    if (status === 'completed') {
        actionButtonsSection.style.display = 'none';
        document.getElementById('reviewSection').style.display = 'block';
    }
}

// 更新订单状态
async function updateOrderStatus(newStatus) {
    if (!currentOrder) return;
    
    if (!confirm(`确定要将订单状态更新为"${newStatus === 'shipped' ? '已发货' : '已收货'}"吗？`)) {
        return;
    }
    
    try {
        const response = await fetch(`/api/orders/${currentOrder.id}/status`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            credentials: 'include',
            body: JSON.stringify({ status: newStatus })
        });
        
        if (!response.ok) {
            throw new Error('更新订单状态失败');
        }
        
        const result = await response.json();
        
        if (result.status === 'success') {
            alert('订单状态更新成功');
            // 重新加载订单详情
            await loadOrderDetails(currentOrder.id);
        } else {
            throw new Error(result.message || '更新订单状态失败');
        }
    } catch (error) {
        console.error('更新订单状态失败:', error);
        alert(error.message || '更新失败，请重试');
    }
}

// 初始化评价表单
function initReviewForm() {
    const reviewForm = document.getElementById('reviewForm');
    if (!reviewForm) return;
    
    // 星级评分
    document.querySelectorAll('.star-rating').forEach(rating => {
        const stars = rating.querySelectorAll('i');
        stars.forEach((star, index) => {
            star.addEventListener('click', function() {
                const ratingValue = parseInt(this.dataset.rating);
                const hiddenInput = rating.parentElement.querySelector('input[type="hidden"]');
                
                // 更新星级显示
                stars.forEach((s, i) => {
                    if (i < ratingValue) {
                        s.classList.add('active');
                    } else {
                        s.classList.remove('active');
                    }
                });
                
                // 更新隐藏输入值
                if (hiddenInput) {
                    hiddenInput.value = ratingValue;
                }
            });
            
            star.addEventListener('mouseenter', function() {
                const ratingValue = parseInt(this.dataset.rating);
                stars.forEach((s, i) => {
                    if (i < ratingValue) {
                        s.style.color = '#ffc107';
                    } else {
                        s.style.color = '#ddd';
                    }
                });
            });
        });
        
        rating.addEventListener('mouseleave', function() {
            const stars = rating.querySelectorAll('i');
            const hiddenInput = rating.parentElement.querySelector('input[type="hidden"]');
            const currentRating = parseInt(hiddenInput?.value || 0);
            
            stars.forEach((s, i) => {
                if (i < currentRating) {
                    s.style.color = '#ffc107';
                } else {
                    s.style.color = '#ddd';
                }
            });
        });
    });
    
    // 表单提交
    reviewForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        await submitReview();
    });
}

// 提交评价
async function submitReview() {
    if (!currentOrder || !currentUser) return;
    
    const serviceRating = parseInt(document.getElementById('serviceRating').value);
    const conditionRating = parseInt(document.getElementById('conditionRating').value);
    const efficiencyRating = parseInt(document.getElementById('efficiencyRating').value);
    const reviewContent = document.getElementById('reviewContent').value.trim();
    
    // 验证评分
    if (serviceRating === 0 || conditionRating === 0 || efficiencyRating === 0) {
        alert('请完成所有评分项');
        return;
    }
    
    const userId = String(currentUser.id || currentUser.user?.id || '');
    const sellerId = String(currentOrder.seller_id || '');
    const buyerId = String(currentOrder.buyer_id || '');
    
    // 确定评价对象（买家评价卖家，卖家评价买家）
    const reviewedUserId = userId === sellerId ? buyerId : sellerId;
    const reviewerRole = userId === sellerId ? 'seller' : 'buyer';
    
    try {
        const response = await fetch('/api/reviews', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            credentials: 'include',
            body: JSON.stringify({
                order_id: currentOrder.id,
                reviewed_user_id: reviewedUserId,
                reviewer_role: reviewerRole,
                service_rating: serviceRating,
                condition_rating: conditionRating,
                efficiency_rating: efficiencyRating,
                review_content: reviewContent
            })
        });
        
        if (!response.ok) {
            throw new Error('提交评价失败');
        }
        
        const result = await response.json();
        
        if (result.status === 'success') {
            alert('评价提交成功');
            // 重新加载评价状态
            await checkReviewStatus();
            // 重置表单
            document.getElementById('reviewForm').reset();
            document.querySelectorAll('.star-rating i').forEach(star => {
                star.classList.remove('active');
            });
        } else {
            throw new Error(result.message || '提交评价失败');
        }
    } catch (error) {
        console.error('提交评价失败:', error);
        alert(error.message || '提交失败，请重试');
    }
}

// 检查评价状态
async function checkReviewStatus() {
    if (!currentOrder || !currentUser) return;
    
    const userId = String(currentUser.id || currentUser.user?.id || '');
    const orderId = currentOrder.id;
    
    try {
        const response = await fetch(`/api/reviews/order/${orderId}`, {
            credentials: 'include'
        });
        
        if (response.ok) {
            const result = await response.json();
            if (result.status === 'success') {
                const reviews = result.reviews || [];
                const myReview = reviews.find(r => String(r.reviewer_id) === userId);
                
                if (myReview) {
                    // 显示已评价内容
                    displayReview(myReview);
                } else {
                    // 显示评价表单
                    document.getElementById('reviewFormContainer').style.display = 'block';
                    document.getElementById('reviewDisplay').style.display = 'none';
                }
            }
        }
    } catch (error) {
        console.error('检查评价状态失败:', error);
    }
}

// 显示评价内容
function displayReview(review) {
    document.getElementById('reviewFormContainer').style.display = 'none';
    document.getElementById('reviewDisplay').style.display = 'block';
    
    const displayContent = document.getElementById('reviewDisplayContent');
    
    const renderStars = (rating) => {
        let stars = '';
        for (let i = 0; i < 5; i++) {
            stars += i < rating 
                ? '<i class="fa fa-star" style="color: #ffc107;"></i>'
                : '<i class="fa fa-star-o" style="color: #ddd;"></i>';
        }
        return stars;
    };
    
    displayContent.innerHTML = `
        <div class="review-rating-item">
            <label>服务态度:</label>
            <span class="review-rating-stars">${renderStars(review.service_rating || 0)}</span>
        </div>
        <div class="review-rating-item">
            <label>书籍品相与描述是否一致:</label>
            <span class="review-rating-stars">${renderStars(review.condition_rating || 0)}</span>
        </div>
        <div class="review-rating-item">
            <label>交易效率:</label>
            <span class="review-rating-stars">${renderStars(review.efficiency_rating || 0)}</span>
        </div>
        ${review.review_content ? `
            <div class="review-content-text">
                <strong>评价内容:</strong><br>
                ${escapeHtml(review.review_content)}
            </div>
        ` : ''}
    `;
}

// 查看书籍详情
function viewBookDetail() {
    if (bookId) {
        window.location.href = `/book1?id=${bookId}`;
    }
}

// 查看订单详情（从订单列表跳转）
function viewOrderDetail(orderId) {
    window.location.href = `/orderDetails?id=${orderId}`;
}

// 加载订单列表
async function loadOrderList() {
    const loadingContainer = document.getElementById('loadingContainer');
    const orderListContainer = document.getElementById('orderListContainer');
    const orderContainer = document.getElementById('orderContainer');
    const errorContainer = document.getElementById('errorContainer');
    
    try {
        loadingContainer.style.display = 'block';
        orderListContainer.style.display = 'none';
        orderContainer.style.display = 'none';
        errorContainer.style.display = 'none';
        
        // 获取订单列表
        const response = await fetch('/api/orders', {
            credentials: 'include'
        });
        
        if (!response.ok) {
            if (response.status === 401) {
                window.location.href = '/login?redirect=/orderDetails';
                return;
            }
            throw new Error('获取订单列表失败');
        }
        
        const result = await response.json();
        
        if (result.status === 'success') {
            const orders = result.orders || [];
            
            if (orders.length === 0) {
                orderListContainer.innerHTML = `
                    <div class="empty-state">
                        <i class="fa fa-inbox"></i>
                        <h3>暂无订单</h3>
                        <p>您还没有任何订单记录</p>
                        <a href="/transactionHistory" class="btn btn-primary">查看交易记录</a>
                    </div>
                `;
            } else {
                renderOrderList(orders);
            }
            
            loadingContainer.style.display = 'none';
            orderListContainer.style.display = 'block';
        } else {
            throw new Error(result.message || '获取订单列表失败');
        }
    } catch (error) {
        console.error('加载订单列表失败:', error);
        loadingContainer.style.display = 'none';
        showError(error.message || '加载失败，请刷新重试');
    }
}

// 渲染订单列表
function renderOrderList(orders) {
    const orderList = document.getElementById('orderList');
    if (!orderList) return;
    
    // 按日期排序（新的在前）
    orders.sort((a, b) => {
        return new Date(b.created_at || 0) - new Date(a.created_at || 0);
    });
    
    const getStatusInfo = (status) => {
        const statusMap = {
            'pending': { text: '待处理', class: 'status-pending', icon: 'fa-clock-o' },
            'shipped': { text: '已发货', class: 'status-shipped', icon: 'fa-truck' },
            'completed': { text: '已完成', class: 'status-completed', icon: 'fa-check-circle' },
            'cancelled': { text: '已取消', class: 'status-cancelled', icon: 'fa-times-circle' }
        };
        return statusMap[status] || { text: status, class: 'status-unknown', icon: 'fa-question' };
    };
    
    let html = '';
    orders.forEach(order => {
        const statusInfo = getStatusInfo(order.status || 'pending');
        const user = getCurrentUser();
        const userId = String(user?.id || user?.user?.id || '');
        const isBuyer = String(order.buyer_id) === userId;
        const roleText = isBuyer ? '买入' : '卖出';
        const counterpartName = isBuyer ? order.seller_name : order.buyer_name;
        
        html += `
            <div class="order-list-item" onclick="viewOrderDetail('${escapeHtml(order.id)}')">
                <div class="order-list-info">
                    <div class="order-list-header">
                        <h5>${escapeHtml(order.book_title || '未知书名')}</h5>
                        <span class="order-role ${isBuyer ? 'buying' : 'selling'}">${roleText}</span>
                    </div>
                    <div class="order-list-details">
                        <p><strong>${isBuyer ? '卖家' : '买家'}:</strong> ${escapeHtml(counterpartName)}</p>
                        <p><strong>价格:</strong> <span class="price">￥${(order.price || 0).toFixed(2)}</span></p>
                        <p><strong>订单号:</strong> ${escapeHtml(order.id)}</p>
                        <p><strong>创建时间:</strong> ${escapeHtml(order.created_at || '')}</p>
                    </div>
                    <div class="order-list-status">
                        <span class="status-badge-small ${statusInfo.class}">
                            <i class="fa ${statusInfo.icon}"></i> ${statusInfo.text}
                        </span>
                    </div>
                </div>
                <div class="order-list-action">
                    <i class="fa fa-chevron-right"></i>
                </div>
            </div>
        `;
    });
    
    orderList.innerHTML = html;
}

// 显示错误信息
function showError(message) {
    const loadingContainer = document.getElementById('loadingContainer');
    const orderContainer = document.getElementById('orderContainer');
    const orderListContainer = document.getElementById('orderListContainer');
    const errorContainer = document.getElementById('errorContainer');
    const errorMessage = document.getElementById('errorMessage');
    
    loadingContainer.style.display = 'none';
    orderContainer.style.display = 'none';
    orderListContainer.style.display = 'none';
    errorContainer.style.display = 'block';
    errorMessage.textContent = message;
}

// HTML转义
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

