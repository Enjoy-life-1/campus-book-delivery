/* 管理员页面JavaScript模块 */
// 使用common.js中定义的apiRequest函数代替import语句
// API请求使用apiRequest函数
// UI工具函数直接在文件中定义或使用main.js中的函数
// 管理员权限检查在需要的地方直接实现

/**
 * 转义HTML特殊字符的函数
 * @param {*} unsafe - 需要转义的内容
 * @returns {string} - 转义后的安全字符串
 */
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
 * 获取分类中文名称
 * @param {string} category - 分类代码
 * @returns {string} - 分类中文名称
 */
function getCategoryName(category) {
    const categoryMap = {
        'textbook': '教材教辅',
        'postgraduate': '考研资料',
        'literature': '文学小说',
        'professional': '专业书籍',
        'other': '其他书籍'
    };
    return categoryMap[category] || category || '其他';
}

/**
 * 获取状态中文名称
 * @param {string} status - 状态代码
 * @returns {string} - 状态中文名称
 */
function getStatusName(status) {
    const statusMap = {
        'available': '在售',
        'sold': '已售出',
        'pending': '待处理',
        'processing': '处理中',
        'completed': '已完成',
        'cancelled': '已取消',
        'active': '上架',
        'inactive': '下架'
    };
    return statusMap[status] || status || '未知';
}

/**
 * 初始化侧边栏导航
 */
function initSidebar() {
    const sidebarToggler = document.querySelector('.sidebar-toggle');
    const sidebar = document.querySelector('.admin-sidebar');
    const mainContent = document.querySelector('.admin-main-content');
    
    if (sidebarToggler && sidebar && mainContent) {
        sidebarToggler.addEventListener('click', function() {
            sidebar.classList.toggle('collapsed');
            mainContent.classList.toggle('sidebar-collapsed');
            
            // 保存侧边栏状态到localStorage（添加错误处理）
        const isCollapsed = sidebar.classList.contains('collapsed');
        try {
            localStorage.setItem('adminSidebarCollapsed', isCollapsed);
        } catch (e) {
            console.warn('无法保存侧边栏状态到localStorage:', e);
        }
        });
        
        // 从localStorage恢复侧边栏状态（添加错误处理）
        let isCollapsed = false;
        try {
            isCollapsed = localStorage.getItem('adminSidebarCollapsed') === 'true';
        } catch (e) {
            console.warn('无法从localStorage读取侧边栏状态:', e);
            isCollapsed = false;
        }
        if (isCollapsed) {
            sidebar.classList.add('collapsed');
            mainContent.classList.add('sidebar-collapsed');
        }
    }
    
    // 初始化侧边栏菜单项激活状态
    const currentPath = window.location.pathname;
    const menuItems = document.querySelectorAll('.sidebar-nav a');
    
    menuItems.forEach(item => {
        const href = item.getAttribute('href');
        if (href && currentPath.includes(href)) {
            item.classList.add('active');
            // 展开父级菜单（如果有）
            const parentMenu = item.closest('.sidebar-submenu');
            if (parentMenu) {
                parentMenu.classList.add('show');
                const parentItem = parentMenu.closest('.sidebar-item');
                if (parentItem) {
                    parentItem.classList.add('menu-open');
                }
            }
        }
    });
}

/**
 * 初始化数据统计图表
 */
// 基本UI工具函数
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type} position-fixed bottom-5 right-5 p-3 rounded shadow-lg`;
    toast.style.zIndex = '9999';
    toast.textContent = message;
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.remove();
    }, 3000);
}

function showLoading(target) {
    const loading = document.createElement('div');
    loading.className = 'loading-indicator d-flex justify-content-center align-items-center';
    loading.innerHTML = '<div class="spinner-border" role="status"></div>';
    
    if (target) {
        target.appendChild(loading);
    } else {
        document.body.appendChild(loading);
    }
}

function hideLoading() {
    const loadings = document.querySelectorAll('.loading-indicator');
    loadings.forEach(loading => loading.remove());
}

function ensureAdmin() {
    const user = getCurrentUser();
    if (!user || user.role !== 'admin') {
        alert('需要管理员权限访问此页面');
        window.location.href = '/';
        return false;
    }
    return true;
}

async function initDashboardCharts() {
    const dashboardCharts = document.getElementById('dashboardCharts');
    if (!dashboardCharts) return;
    
    // 默认模拟数据，用于降级显示
    const defaultStats = {
        bookCounts: {
            '文学类': 120,
            '科技类': 85,
            '教育类': 200,
            '生活类': 65,
            '艺术类': 45
        },
        userGrowth: {
            '1月': 28,
            '2月': 42,
            '3月': 65,
            '4月': 80,
            '5月': 95,
            '6月': 110
        }
    };
    
    let stats = {};
    
    try {
        // 尝试获取统计数据
        const response = await apiRequest('/api/admin/stats', {
            method: 'GET'
        });
        stats = response && response.data ? response.data : {};
    } catch (error) {
        console.warn('无法获取统计数据，使用默认数据:', error);
        // 使用默认模拟数据
        stats = defaultStats;
    }
    
    // 如果获取的数据不完整，使用默认数据补充
    stats.bookCounts = stats.bookCounts || defaultStats.bookCounts;
    stats.userGrowth = stats.userGrowth || defaultStats.userGrowth;
    
    // 初始化书籍数量图表
    if (stats.bookCounts && typeof Chart !== 'undefined' && typeof Object.keys === 'function' && typeof Object.values === 'function') {
        const bookChartCtx = document.getElementById('bookCountChart');
        if (bookChartCtx) {
            new Chart(bookChartCtx, {
                type: 'bar',
                data: {
                    labels: Object.keys(stats.bookCounts),
                    datasets: [{
                        label: '书籍数量',
                        data: Object.values(stats.bookCounts),
                        backgroundColor: '#007bff'
                    }]
                },
                options: {
                    responsive: true,
                    scales: {
                        y: {
                            beginAtZero: true
                        }
                    }
                }
            });
        }
    }
    
    // 初始化用户增长图表
    if (stats.userGrowth && typeof Chart !== 'undefined' && typeof Object.keys === 'function' && typeof Object.values === 'function') {
        const userChartCtx = document.getElementById('userGrowthChart');
        if (userChartCtx) {
            new Chart(userChartCtx, {
                type: 'line',
                data: {
                    labels: Object.keys(stats.userGrowth),
                    datasets: [{
                        label: '用户增长',
                        data: Object.values(stats.userGrowth),
                        borderColor: '#28a745',
                        tension: 0.1
                    }]
                },
                options: {
                    responsive: true,
                    scales: {
                        y: {
                            beginAtZero: true
                        }
                    }
                }
            });
        }
    }
}

/**
 * 初始化用户管理功能
 */
async function initUserManagement() {
    const userManagementSection = document.getElementById('userManagement');
    if (!userManagementSection) return;
    
    try {
        // 加载用户列表
        const response = await apiRequest('/api/admin/users', {
            method: 'GET'
        });
        const users = response.users || [];
        
        const userTableBody = document.getElementById('userTableBody');
        if (userTableBody) {
            if (users.length === 0) {
                userTableBody.innerHTML = '<tr><td colspan="6" class="text-center">暂无用户数据</td></tr>';
                return;
            }
            
            let html = '';
            users.forEach(user => {
                html += `
                    <tr>
                        <td>${user.id}</td>
                        <td>${user.username}</td>
                        <td>${user.email}</td>
                        <td>${user.role === 'admin' ? '管理员' : '普通用户'}</td>
                        <td>${new Date(user.created_at).toLocaleString()}</td>
                        <td>
                            <div class="btn-group">
                                <button class="btn btn-sm btn-primary" onclick="editUser(${user.id})"><i class="fa fa-edit"></i></button>
                                <button class="btn btn-sm btn-danger" onclick="deleteUser(${user.id})"><i class="fa fa-trash"></i></button>
                            </div>
                        </td>
                    </tr>
                `;
            });
            
            userTableBody.innerHTML = html;
        }
    } catch (error) {
        console.error('加载用户列表失败:', error);
        showToast('加载用户列表失败，请稍后重试', 'error');
    }
}

/**
 * 初始化书籍管理功能
 */
async function initBookManagement() {
    const bookManagementSection = document.getElementById('bookManagement');
    if (!bookManagementSection) return;
    
    try {
        // 加载书籍列表
        const response = await apiRequest('/api/books', {
            method: 'GET'
        });
        const books = response.books || [];
        
        const bookTableBody = document.getElementById('bookTableBody');
        if (bookTableBody) {
            if (books.length === 0) {
                bookTableBody.innerHTML = '<tr><td colspan="6" class="text-center">暂无书籍数据</td></tr>';
                return;
            }
            
            let html = '';
            books.forEach(book => {
                html += `
                    <tr>
                        <td>${book.id}</td>
                        <td>${book.title}</td>
                        <td>${book.author}</td>
                        <td>¥${book.price}</td>
                        <td>${book.status === 'active' ? '上架' : '下架'}</td>
                        <td>
                            <div class="btn-group">
                                <button class="btn btn-sm btn-primary" onclick="editBook(${book.id})"><i class="fa fa-edit"></i></button>
                                <button class="btn btn-sm btn-danger" onclick="deleteBook(${book.id})"><i class="fa fa-trash"></i></button>
                            </div>
                        </td>
                    </tr>
                `;
            });
            
            bookTableBody.innerHTML = html;
        }
    } catch (error) {
        console.error('加载书籍列表失败:', error);
        showToast('加载书籍列表失败，请稍后重试', 'error');
    }
}

/**
 * 初始化订单管理功能
 */
async function initOrderManagement() {
    const orderManagementSection = document.getElementById('orderManagement');
    if (!orderManagementSection) return;
    
    try {
        // 加载订单列表
        const response = await apiRequest('/api/admin/orders', {
            method: 'GET'
        });
        const orders = response.orders || [];
        
        const orderTableBody = document.getElementById('orderTableBody');
        if (orderTableBody) {
            if (orders.length === 0) {
                orderTableBody.innerHTML = '<tr><td colspan="6" class="text-center">暂无订单数据</td></tr>';
                return;
            }
            
            let html = '';
            orders.forEach(order => {
                html += `
                    <tr>
                        <td>${order.order_id}</td>
                        <td>${order.username}</td>
                        <td>¥${order.total_amount}</td>
                        <td>${formatOrderStatus(order.status)}</td>
                        <td>${new Date(order.created_at).toLocaleString()}</td>
                        <td>
                            <div class="btn-group">
                                <button class="btn btn-sm btn-primary" onclick="viewOrder(${order.id})"><i class="fa fa-eye"></i></button>
                                ${order.status === 'pending' ? 
                                    `<button class="btn btn-sm btn-success" onclick="processOrder(${order.id})"><i class="fa fa-check"></i></button>` : 
                                    ''
                                }
                            </div>
                        </td>
                    </tr>
                `;
            });
            
            orderTableBody.innerHTML = html;
        }
    } catch (error) {
        console.error('加载订单列表失败:', error);
        showToast('加载订单列表失败，请稍后重试', 'error');
    }
}

/**
 * 格式化订单状态
 * @param {string} status - 订单状态
 * @returns {string} - 格式化后的订单状态文本
 */
function formatOrderStatus(status) {
    const statusMap = {
        'pending': '待处理',
        'processing': '处理中',
        'shipped': '已发货',
        'delivered': '已送达',
        'cancelled': '已取消',
        'completed': '已完成'
    };
    return statusMap[status] || status;
}

/**
 * 初始化管理员页面功能
 */
async function initAdminPage() {
    // 确保用户是管理员
    if (!ensureAdmin()) {
        return;
    }
    
    // 初始化侧边栏
    initSidebar();
    
    // 根据当前页面初始化不同功能
    initDashboardCharts();
    initUserManagement();
    initBookManagement();
    initOrderManagement();
    
    // 为全局操作添加事件监听
    document.addEventListener('click', function(e) {
        // 处理搜索按钮点击
        if (e.target.closest('.search-btn')) {
            const searchInput = document.querySelector('.search-input');
            if (searchInput && searchInput.value.trim()) {
                // 执行搜索逻辑
                showToast('搜索功能开发中', 'info');
            }
        }
    });
}

/**
 * 页面加载完成后初始化
 */
document.addEventListener('DOMContentLoaded', function() {
    // 仅在管理员页面执行初始化
    if (window.location.pathname.includes('/admin')) {
        initAdminPage();
    }
});

// 获取状态名称
function getStatusName(status) {
    const statusMap = {
        'available': '在售',
        'sold': '已售',
        'pending': '待审核',
        'active': '在售',
        'inactive': '下架'
    };
    return statusMap[status] || status || '未知';
}

// 导出公共函数，便于其他模块调用
// 移除export语句，确保浏览器兼容性

// 为了支持内联的onclick事件，将一些函数挂载到window对象
window.editUser = function(id) {
    showToast('编辑用户功能开发中', 'info');
};

window.deleteUser = function(id) {
    if (confirm('确定要删除该用户吗？')) {
        apiRequest(`/api/admin/users/${id}`, {
            method: 'DELETE'
        })
            .then(() => {
                showToast('用户删除成功', 'success');
                initUserManagement(); // 重新加载用户列表
            })
            .catch(() => {
                showToast('用户删除失败，请稍后重试', 'error');
            });
    }
};

window.editBook = function(id) {
    showToast('编辑书籍功能开发中', 'info');
};

window.deleteBook = function(id) {
    if (confirm('确定要删除该书吗？')) {
        apiRequest(`/api/admin/books/${id}`, {
            method: 'DELETE'
        })
            .then(() => {
                showToast('书籍删除成功', 'success');
                initBookManagement(); // 重新加载书籍列表
            })
            .catch(() => {
                showToast('书籍删除失败，请稍后重试', 'error');
            });
    }
};

// 将批量操作函数挂载到window对象
window.exportSelectedBooks = exportSelectedBooks;
window.exportAllBooks = exportAllBooks;
window.deleteSelectedBooks = deleteSelectedBooks;
window.deleteAllBooks = deleteAllBooks;

window.viewOrder = function(id) {
    showToast('查看订单功能开发中', 'info');
};

window.processOrder = function(id) {
    if (confirm('确定要处理该订单吗？')) {
        apiRequest(`/api/admin/orders/${id}/process`, {
            method: 'PUT'
        })
            .then(() => {
                showToast('订单处理成功', 'success');
                initOrderManagement(); // 重新加载订单列表
            })
            .catch(() => {
                showToast('订单处理失败，请稍后重试', 'error');
            });
    }
};

// 以下是admin.html页面特定功能

/**
 * 侧边栏切换功能
 */
function initSidebarToggle() {
    const toggleBtn = document.getElementById('toggleSidebar');
    const sidebar = document.querySelector('.sidebar');
    const mainContent = document.querySelector('.main-content');
    
    if (toggleBtn && sidebar && mainContent) {
        toggleBtn.addEventListener('click', () => {
            sidebar.classList.toggle('active');
            mainContent.classList.toggle('sidebar-collapsed');
        });
    }
}

/**
 * 区域切换功能
 */
function initSectionNavigation() {
    const navLinks = document.querySelectorAll('.nav-link');
    const sections = document.querySelectorAll('.section');
    const pageTitle = document.getElementById('pageTitle');
    
    navLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            const href = link.getAttribute('href');
            const dataSection = link.getAttribute('data-section');
            
            // 如果链接有实际的URL（不是#或空），允许正常跳转
            if (href && href !== '#' && !href.startsWith('javascript:')) {
                // 允许正常跳转，不阻止默认行为
                return;
            }
            
            // 如果没有data-section属性，也不处理
            if (!dataSection) {
                return;
            }
            
            // 阻止默认行为（仅对页面内切换的链接）
            e.preventDefault();
            
            // 更新激活状态
            navLinks.forEach(l => l.classList.remove('active'));
            link.classList.add('active');
            
            // 隐藏所有区域
            sections.forEach(section => section.style.display = 'none');
            
            // 显示对应区域
            const sectionId = dataSection + '-section';
            const targetSection = document.getElementById(sectionId);
            if (targetSection) {
                targetSection.style.display = 'block';
                
                // 更新页面标题
                if (pageTitle) {
                    pageTitle.textContent = link.textContent.trim();
                }
                
                // 重新初始化该区域的功能
                if (sectionId === 'dashboard-section') {
                    initDashboardStats();
                    initCharts();
                } else if (sectionId === 'users-section') {
                    initUsersTable();
                } else if (sectionId === 'books-section') {
                    initBooksTable();
                } else if (sectionId === 'categories-section') {
                    initCategoriesTable();
                }
            }
        });
    });
}

/**
 * 初始化仪表盘统计数据
 */
async function initDashboardStats() {
    const updateStatValue = (ids, value) => {
        ids.forEach(id => {
            const el = document.getElementById(id);
            if (el) {
                el.textContent = Number(value || 0).toLocaleString();
            }
        });
    };
    
    try {
        const response = await fetch('/api/admin/stats', {
            credentials: 'include'
        });
        if (!response.ok) {
            throw new Error('获取统计数据失败');
        }
        const result = await response.json();
        const stats = result.stats || {};
        
        updateStatValue(['totalBooksCount', 'totalBooks'], stats.totalBooks);
        updateStatValue(['registeredUsersCount', 'totalUsers'], stats.registeredUsers);
        updateStatValue(['monthlySalesCount', 'totalTransactions'], stats.monthlySales);
        updateStatValue(['pendingTasksCount', 'totalViews'], stats.pendingTasks);
    } catch (error) {
        console.error('获取统计数据失败:', error);
    }
}

/**
 * 初始化图表
 */
function initCharts() {
    // 用户增长趋势图表
    const userGrowthCtx = document.getElementById('userGrowthChart');
    // 确保canvas元素存在且Chart库已加载
    if (userGrowthCtx && typeof Chart !== 'undefined') {
        new Chart(userGrowthCtx, {
            type: 'line',
            data: {
                labels: ['1月', '2月', '3月', '4月', '5月', '6月'],
                datasets: [{
                    label: '用户增长',
                    data: [120, 190, 300, 500, 800, 1200],
                    borderColor: '#007bff',
                    backgroundColor: 'rgba(0, 123, 255, 0.1)',
                    tension: 0.3,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false
            }
        });
    }
    
    // 书籍分类分布图表
    const bookCategoryCtx = document.getElementById('bookCategoryChart');
    // 确保canvas元素存在且Chart库已加载
    if (bookCategoryCtx && typeof Chart !== 'undefined') {
        new Chart(bookCategoryCtx, {
            type: 'doughnut',
            data: {
                labels: ['教材教辅', '考研资料', '文学小说', '专业书籍', '其他书籍'],
                datasets: [{
                    data: [35, 25, 20, 15, 5],
                    backgroundColor: ['#007bff', '#28a745', '#ffc107', '#dc3545', '#6c757d']
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'right'
                    }
                }
            }
        });
    }
}

/**
 * 初始化用户表格
 */
async function initUsersTable() {
    try {
        // 模拟用户数据
        const users = [
            { id: 1, username: 'admin', role: 'admin', registered: '2024-01-01', status: 'active' },
            { id: 2, username: 'student1', role: 'student', registered: '2024-01-15', status: 'active' },
            { id: 3, username: 'student2', role: 'student', registered: '2024-02-01', status: 'active' }
        ];
        
        const tableBody = document.getElementById('usersTableBody');
        if (tableBody) {
            if (users.length === 0) {
                tableBody.innerHTML = '<tr><td colspan="6" class="text-center">暂无用户数据</td></tr>';
                document.getElementById('usersTableEmpty').style.display = 'block';
            } else {
                let html = '';
                users.forEach(user => {
                    html += `
                        <tr>
                            <td>${user.id}</td>
                            <td>${user.username}</td>
                            <td>${user.role === 'admin' ? '管理员' : '学生'}</td>
                            <td>${user.registered}</td>
                            <td>
                                <span class="badge bg-success">${user.status === 'active' ? '活跃' : '禁用'}</span>
                            </td>
                            <td>
                                <div class="action-buttons">
                                    <button class="btn btn-sm btn-primary" onclick="editUser(${user.id})"><i class="fa fa-edit"></i> 编辑</button>
                                    <button class="btn btn-sm btn-danger" onclick="deleteUser(${user.id})"><i class="fa fa-trash"></i> 删除</button>
                                </div>
                            </td>
                        </tr>
                    `;
                });
                tableBody.innerHTML = html;
                document.getElementById('usersTableEmpty').style.display = 'none';
            }
        }
    } catch (error) {
        console.error('初始化用户表格失败:', error);
    }
}

// 存储所有书籍数据
let allBooksData = [];

/**
 * 初始化书籍表格
 */
async function initBooksTable() {
    try {
        // 从API加载真实数据
        const response = await fetch('/api/books?page=1&page_size=10000&include_sold=true', {
            credentials: 'include'
        });
        
        if (!response.ok) {
            throw new Error('获取书籍数据失败');
        }
        
        const result = await response.json();
        allBooksData = result.books || [];
        
        renderBooksTable(allBooksData);
        initBookSelection();
    } catch (error) {
        console.error('初始化书籍表格失败:', error);
        showToast('加载书籍数据失败，请稍后重试', 'error');
    }
}

/**
 * 渲染书籍表格
 */
function renderBooksTable(books) {
    const tableBody = document.getElementById('booksTableBody');
    const emptyState = document.getElementById('booksTableEmpty');
    
    if (!tableBody) return;
    
    if (books.length === 0) {
        tableBody.innerHTML = '<tr><td colspan="10" class="text-center">暂无书籍数据</td></tr>';
        if (emptyState) emptyState.style.display = 'block';
        return;
    }
    
    if (emptyState) emptyState.style.display = 'none';
    
    let html = '';
    books.forEach(book => {
        const statusBadge = book.status === 'available' 
            ? '<span class="badge bg-success">在售</span>' 
            : book.status === 'sold'
            ? '<span class="badge bg-secondary">已售</span>'
            : '<span class="badge bg-warning">待审核</span>';
        
        html += `
            <tr>
                <td class="checkbox-col">
                    <input type="checkbox" class="book-checkbox" data-book-id="${book.id}">
                </td>
                <td>${book.id || '-'}</td>
                <td>${escapeHtml(book.title || '-')}</td>
                <td>${escapeHtml(book.author || '-')}</td>
                <td>${escapeHtml(getCategoryName(book.category || 'other'))}</td>
                <td>¥${parseFloat(book.price || 0).toFixed(2)}</td>
                <td>${book.stock || 0}</td>
                <td>${formatDate(book.created_at || '')}</td>
                <td>${statusBadge}</td>
                <td>
                    <div class="action-buttons">
                        <button class="action-btn-small view" title="查看" onclick="viewBook('${book.id}')">
                            <i class="fas fa-eye"></i>
                        </button>
                        <button class="action-btn-small edit" title="编辑" onclick="editBook('${book.id}')">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button class="action-btn-small delete" title="删除" onclick="confirmDeleteBook('${book.id}')">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </td>
            </tr>
        `;
    });
    tableBody.innerHTML = html;
    
    // 重新初始化选择功能
    initBookSelection();
}

/**
 * 格式化日期
 */
function formatDate(dateString) {
    if (!dateString) return '-';
    try {
        const date = new Date(dateString);
        return date.toLocaleString('zh-CN', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit'
        });
    } catch (e) {
        return dateString;
    }
}

/**
 * 初始化书籍选择功能
 */
function initBookSelection() {
    // 全选复选框
    const selectAllCheckboxes = document.querySelectorAll('.select-all-checkbox');
    selectAllCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            const isChecked = this.checked;
            const bookCheckboxes = document.querySelectorAll('.book-checkbox');
            bookCheckboxes.forEach(cb => {
                cb.checked = isChecked;
            });
            updateSelectionState();
        });
    });
    
    // 单个复选框
    const bookCheckboxes = document.querySelectorAll('.book-checkbox');
    bookCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            updateSelectionState();
        });
    });
    
    // 更新选择状态
    updateSelectionState();
}

/**
 * 更新选择状态
 */
function updateSelectionState() {
    const bookCheckboxes = document.querySelectorAll('.book-checkbox');
    const checkedBoxes = document.querySelectorAll('.book-checkbox:checked');
    const selectedCount = checkedBoxes.length;
    
    // 更新选中数量显示
    const selectedCountEl = document.getElementById('selectedCount');
    if (selectedCountEl) {
        selectedCountEl.textContent = `已选择: ${selectedCount} 项`;
    }
    
    // 更新全选复选框状态
    const selectAllCheckboxes = document.querySelectorAll('.select-all-checkbox');
    selectAllCheckboxes.forEach(cb => {
        cb.checked = bookCheckboxes.length > 0 && selectedCount === bookCheckboxes.length;
        cb.indeterminate = selectedCount > 0 && selectedCount < bookCheckboxes.length;
    });
    
    // 更新按钮状态
    const exportSelectedBtn = document.getElementById('exportSelectedBtn');
    const deleteSelectedBtn = document.getElementById('deleteSelectedBtn');
    
    if (exportSelectedBtn) {
        exportSelectedBtn.disabled = selectedCount === 0;
    }
    if (deleteSelectedBtn) {
        deleteSelectedBtn.disabled = selectedCount === 0;
    }
}

/**
 * 获取选中的书籍ID
 */
function getSelectedBookIds() {
    const checkedBoxes = document.querySelectorAll('.book-checkbox:checked');
    return Array.from(checkedBoxes).map(cb => cb.getAttribute('data-book-id'));
}

/**
 * 导出选中书籍为CSV
 */
async function exportSelectedBooks() {
    const selectedIds = getSelectedBookIds();
    if (selectedIds.length === 0) {
        showToast('请先选择要导出的书籍', 'warning');
        return;
    }
    
    const selectedBooks = allBooksData.filter(book => selectedIds.includes(book.id));
    exportBooksToCSV(selectedBooks, '选中书籍');
}

/**
 * 导出全部书籍为CSV
 */
async function exportAllBooks() {
    if (allBooksData.length === 0) {
        showToast('没有可导出的书籍', 'warning');
        return;
    }
    
    if (!confirm(`确定要导出全部 ${allBooksData.length} 本书籍吗？`)) {
        return;
    }
    
    exportBooksToCSV(allBooksData, '全部书籍');
}

/**
 * 导出书籍为CSV文件
 */
function exportBooksToCSV(books, filename) {
    if (books.length === 0) {
        showToast('没有可导出的数据', 'warning');
        return;
    }
    
    // CSV表头
    const headers = ['ID', '书名', '作者', '分类', '价格', '库存', '状态', '发布者', '发布时间', '描述'];
    
    // 转换数据
    const csvRows = [
        headers.join(','),
        ...books.map(book => {
            const row = [
                book.id || '',
                `"${(book.title || '').replace(/"/g, '""')}"`,
                `"${(book.author || '').replace(/"/g, '""')}"`,
                `"${getCategoryName(book.category || 'other')}"`,
                book.price || 0,
                book.stock || 0,
                book.status === 'available' ? '在售' : book.status === 'sold' ? '已售' : '待审核',
                `"${(book.owner_name || '').replace(/"/g, '""')}"`,
                `"${(book.created_at || '').replace(/"/g, '""')}"`,
                `"${((book.description || book.desc || '').replace(/"/g, '""')).substring(0, 100)}"`
            ];
            return row.join(',');
        })
    ];
    
    // 创建CSV内容
    const csvContent = csvRows.join('\n');
    
    // 添加BOM以支持中文
    const BOM = '\uFEFF';
    const blob = new Blob([BOM + csvContent], { type: 'text/csv;charset=utf-8;' });
    
    // 创建下载链接
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', `${filename}_${new Date().toISOString().split('T')[0]}.csv`);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    showToast(`成功导出 ${books.length} 本书籍`, 'success');
}

/**
 * 删除选中书籍
 */
async function deleteSelectedBooks() {
    const selectedIds = getSelectedBookIds();
    if (selectedIds.length === 0) {
        showToast('请先选择要删除的书籍', 'warning');
        return;
    }
    
    if (!confirm(`确定要删除选中的 ${selectedIds.length} 本书籍吗？此操作不可撤销！`)) {
        return;
    }
    
    try {
        showToast('正在删除...', 'info');
        let successCount = 0;
        let failCount = 0;
        
        // 批量删除
        for (const bookId of selectedIds) {
            try {
                const response = await fetch(`/api/books/${bookId}`, {
                    method: 'DELETE',
                    credentials: 'include'
                });
                
                const result = await response.json();
                if (result.status === 'success') {
                    successCount++;
                } else {
                    failCount++;
                }
            } catch (error) {
                console.error(`删除书籍 ${bookId} 失败:`, error);
                failCount++;
            }
        }
        
        if (successCount > 0) {
            showToast(`成功删除 ${successCount} 本书籍${failCount > 0 ? `，${failCount} 本失败` : ''}`, 'success');
            // 重新加载书籍列表
            await initBooksTable();
        } else {
            showToast('删除失败，请稍后重试', 'error');
        }
    } catch (error) {
        console.error('批量删除失败:', error);
        showToast('删除操作失败，请稍后重试', 'error');
    }
}

/**
 * 删除全部书籍
 */
async function deleteAllBooks() {
    if (allBooksData.length === 0) {
        showToast('没有可删除的书籍', 'warning');
        return;
    }
    
    if (!confirm(`警告：确定要删除全部 ${allBooksData.length} 本书籍吗？此操作不可撤销！`)) {
        return;
    }
    
    // 二次确认
    if (!confirm('此操作将永久删除所有书籍数据，请再次确认！')) {
        return;
    }
    
    try {
        showToast('正在删除全部书籍...', 'info');
        const allIds = allBooksData.map(book => book.id);
        let successCount = 0;
        let failCount = 0;
        
        // 批量删除
        for (const bookId of allIds) {
            try {
                const response = await fetch(`/api/books/${bookId}`, {
                    method: 'DELETE',
                    credentials: 'include'
                });
                
                const result = await response.json();
                if (result.status === 'success') {
                    successCount++;
                } else {
                    failCount++;
                }
            } catch (error) {
                console.error(`删除书籍 ${bookId} 失败:`, error);
                failCount++;
            }
        }
        
        if (successCount > 0) {
            showToast(`成功删除 ${successCount} 本书籍${failCount > 0 ? `，${failCount} 本失败` : ''}`, 'success');
            // 重新加载书籍列表
            await initBooksTable();
        } else {
            showToast('删除失败，请稍后重试', 'error');
        }
    } catch (error) {
        console.error('删除全部书籍失败:', error);
        showToast('删除操作失败，请稍后重试', 'error');
    }
}

/**
 * 初始化分类表格
 */
async function initCategoriesTable() {
    try {
        // 模拟分类数据
        const categories = [
            { id: 1, name: '教材教辅', code: 'textbook', bookCount: 120 },
            { id: 2, name: '考研资料', code: 'postgraduate', bookCount: 85 },
            { id: 3, name: '文学小说', code: 'literature', bookCount: 67 },
            { id: 4, name: '专业书籍', code: 'professional', bookCount: 45 },
            { id: 5, name: '其他书籍', code: 'other', bookCount: 23 }
        ];
        
        const tableBody = document.getElementById('categoriesTableBody');
        if (tableBody) {
            let html = '';
            categories.forEach(category => {
                html += `
                    <tr>
                        <td>${category.id}</td>
                        <td>${category.name}</td>
                        <td>${category.code}</td>
                        <td>${category.bookCount}</td>
                        <td>
                            <div class="action-buttons">
                                <button class="btn btn-sm btn-primary" onclick="editCategory(${category.id})"><i class="fa fa-edit"></i> 编辑</button>
                                <button class="btn btn-sm btn-danger" onclick="deleteCategory(${category.id})"><i class="fa fa-trash"></i> 删除</button>
                            </div>
                        </td>
                    </tr>
                `;
            });
            tableBody.innerHTML = html;
        }
    } catch (error) {
        console.error('初始化分类表格失败:', error);
    }
}

/**
 * 初始化搜索和过滤功能
 */
function initSearchAndFilter() {
    // 用户搜索
    const userSearchInput = document.getElementById('userSearchInput');
    if (userSearchInput) {
        userSearchInput.addEventListener('input', debounce(() => {
            filterUsers();
        }, 300));
    }
    
    // 用户角色过滤
    const userRoleFilter = document.getElementById('userRoleFilter');
    if (userRoleFilter) {
        userRoleFilter.addEventListener('change', () => {
            filterUsers();
        });
    }
    
    // 书籍搜索和筛选
    const bookSearchInput = document.getElementById('bookSearchInput');
    const bookCategoryFilter = document.getElementById('bookCategoryFilter');
    const priceRangeFilter = document.getElementById('priceRangeFilter');
    const publishTimeFilter = document.getElementById('publishTimeFilter');
    
    if (bookSearchInput) {
        // 实时搜索（输入时自动触发）
        bookSearchInput.addEventListener('input', debounce(() => {
            filterBooks();
        }, 300));
        
        // 回车键搜索
        bookSearchInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                filterBooks();
            }
        });
    }
    
    if (bookCategoryFilter) {
        bookCategoryFilter.addEventListener('change', () => {
            filterBooks();
        });
    }
    
    if (priceRangeFilter) {
        priceRangeFilter.addEventListener('change', () => {
            filterBooks();
        });
    }
    
    if (publishTimeFilter) {
        publishTimeFilter.addEventListener('change', () => {
            filterBooks();
        });
    }
    
    // 分类搜索
    const categorySearchInput = document.getElementById('categorySearchInput');
    if (categorySearchInput) {
        categorySearchInput.addEventListener('input', debounce(() => {
            filterCategories();
        }, 300));
    }
}

/**
 * 过滤用户
 */
function filterUsers() {
    // 实际项目中应通过API获取过滤后的数据
    console.log('过滤用户:', {
        search: document.getElementById('userSearchInput')?.value,
        role: document.getElementById('userRoleFilter')?.value
    });
}

/**
 * 过滤书籍
 */
async function filterBooks() {
    const search = document.getElementById('bookSearchInput')?.value || '';
    const category = document.getElementById('bookCategoryFilter')?.value || 'all';
    const priceRange = document.getElementById('priceRangeFilter')?.value || 'all';
    
    // 构建搜索参数
    const params = new URLSearchParams();
    params.append('page', '1');
    params.append('page_size', '1000');
    if (search) params.append('search', search);
    if (category && category !== 'all') params.append('category', category);
    if (priceRange && priceRange !== 'all') params.append('priceRange', priceRange);
    
    try {
        const response = await fetch(`/api/books?${params.toString()}`, {
            credentials: 'include'
        });
        
        if (!response.ok) {
            throw new Error('获取书籍数据失败');
        }
        
        const result = await response.json();
        const books = result.books || [];
        
        const bookTableBody = document.getElementById('booksTableBody');
        const emptyState = document.getElementById('booksTableEmpty');
        
        if (bookTableBody) {
            if (books.length === 0) {
                bookTableBody.innerHTML = '';
                if (emptyState) {
                    emptyState.classList.add('active');
                }
                return;
            }
            
            if (emptyState) {
                emptyState.classList.remove('active');
            }
            
            let html = '';
            books.forEach(book => {
                const categoryName = getCategoryName(book.category);
                const statusText = getStatusName(book.status);
                const statusClass = book.status === 'available' ? 'success' : 'secondary';
                
                html += `
                    <tr>
                        <td><input type="checkbox" class="book-checkbox" data-book-id="${book.id}"></td>
                        <td>${escapeHtml(book.id || '')}</td>
                        <td>${escapeHtml(book.title || '')}</td>
                        <td>${escapeHtml(book.author || '')}</td>
                        <td>${escapeHtml(categoryName)}</td>
                        <td>¥${parseFloat(book.price || 0).toFixed(2)}</td>
                        <td>${book.stock !== undefined ? book.stock : '-'}</td>
                        <td>${escapeHtml(book.created_at || book.createTime || '')}</td>
                        <td>
                            <span class="badge bg-${statusClass}">${statusText}</span>
                        </td>
                        <td>
                            <div class="action-buttons">
                                <button class="action-btn-small view" title="查看" onclick="viewBook('${book.id}')">
                                    <i class="fas fa-eye"></i>
                                </button>
                                <button class="action-btn-small edit" title="编辑" onclick="editBook('${book.id}')">
                                    <i class="fas fa-edit"></i>
                                </button>
                                <button class="action-btn-small delete" title="删除" onclick="deleteBook('${book.id}')">
                                    <i class="fas fa-trash"></i>
                                </button>
                            </div>
                        </td>
                    </tr>
                `;
            });
            
            bookTableBody.innerHTML = html;
        }
    } catch (error) {
        console.error('过滤书籍失败:', error);
        if (typeof showToast === 'function') {
            showToast('搜索失败，请稍后重试', 'error');
        } else {
            alert('搜索失败，请稍后重试');
        }
    }
}

/**
 * 过滤分类
 */
function filterCategories() {
    // 实际项目中应通过API获取过滤后的数据
    console.log('过滤分类:', {
        search: document.getElementById('categorySearchInput')?.value
    });
}

/**
 * 防抖函数
 */
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

/**
 * 初始化模态框功能
 */
function initModals() {
    // 添加用户模态框
    const addUserBtn = document.getElementById('addUserBtn');
    const addUserModal = document.getElementById('addUserModal');
    const closeAddUserModal = document.getElementById('closeAddUserModal');
    const cancelAddUserBtn = document.getElementById('cancelAddUserBtn');
    
    if (addUserBtn && addUserModal) {
        addUserBtn.addEventListener('click', () => {
            addUserModal.classList.add('active');
        });
    }
    
    const closeModal = () => {
        addUserModal.classList.remove('active');
    };
    
    if (closeAddUserModal) closeAddUserModal.addEventListener('click', closeModal);
    if (cancelAddUserBtn) cancelAddUserBtn.addEventListener('click', closeModal);
    
    // 确认添加用户
    const confirmAddUserBtn = document.getElementById('confirmAddUserBtn');
    const addUserForm = document.getElementById('addUserForm');
    
    if (confirmAddUserBtn && addUserForm) {
        confirmAddUserBtn.addEventListener('click', () => {
            if (addUserForm.checkValidity()) {
                // 模拟添加用户
                showToast('用户添加成功', 'success');
                closeModal();
                initUsersTable(); // 重新加载用户列表
            }
        });
    }
}

/**
 * 初始化系统设置功能
 */
function initSystemSettings() {
    const settingsForm = document.getElementById('settingsForm');
    if (settingsForm) {
        settingsForm.addEventListener('submit', (e) => {
            e.preventDefault();
            
            // 模拟保存设置
            const settings = {
                systemName: document.getElementById('systemName').value,
                pageSize: document.getElementById('pageSize').value,
                cacheDays: document.getElementById('cacheDays').value,
                enableRegister: document.getElementById('enableRegister').checked
            };
            
            console.log('保存设置:', settings);
            showToast('设置保存成功', 'success');
        });
    }
}

/**
 * 退出登录
 */
window.logout = function() {
    if (confirm('确定要退出登录吗？')) {
        // 实际项目中应调用退出登录API
        window.location.href = '/login';
    }
};

/**
 * 编辑用户
 */
window.editUser = function(id) {
    console.log('编辑用户:', id);
    showToast('编辑用户功能开发中', 'info');
};

/**
 * 删除用户
 */
window.deleteUser = function(id) {
    if (confirm('确定要删除该用户吗？')) {
        console.log('删除用户:', id);
        showToast('用户删除成功', 'success');
        initUsersTable(); // 重新加载用户列表
    }
};

/**
 * 查看书籍详情
 */
window.viewBook = async function(id) {
    try {
        const response = await fetch(`/api/books/${id}`, {
            credentials: 'include'
        });
        
        if (!response.ok) {
            throw new Error('获取书籍详情失败');
        }
        
        const result = await response.json();
        const book = result.book;
        
        if (!book) {
            alert('书籍不存在');
            return;
        }
        
        const modal = document.getElementById('view-book-modal');
        const content = document.getElementById('bookDetailContent');
        
        content.innerHTML = `
            <div style="line-height: 1.8;">
                <p><strong>ID:</strong> ${escapeHtml(book.id || '')}</p>
                <p><strong>书名:</strong> ${escapeHtml(book.title || '')}</p>
                <p><strong>作者:</strong> ${escapeHtml(book.author || '')}</p>
                <p><strong>分类:</strong> ${escapeHtml(getCategoryName(book.category))}</p>
                <p><strong>价格:</strong> ¥${parseFloat(book.price || 0).toFixed(2)}</p>
                <p><strong>状态:</strong> ${getStatusName(book.status)}</p>
                <p><strong>卖家:</strong> ${escapeHtml(book.owner_name || book.seller || '')}</p>
                <p><strong>发布时间:</strong> ${escapeHtml(book.created_at || book.createTime || '')}</p>
                <p><strong>描述:</strong></p>
                <p style="background: #f5f5f5; padding: 10px; border-radius: 4px; margin-top: 5px;">
                    ${escapeHtml(book.description || book.desc || '暂无描述')}
                </p>
            </div>
        `;
        
        modal.classList.add('active');
    } catch (error) {
        console.error('查看书籍失败:', error);
        alert('获取书籍详情失败，请稍后重试');
    }
};

/**
 * 编辑书籍
 */
window.editBook = async function(id) {
    try {
        const response = await fetch(`/api/books/${id}`, {
            credentials: 'include'
        });
        
        if (!response.ok) {
            throw new Error('获取书籍详情失败');
        }
        
        const result = await response.json();
        const book = result.book;
        
        if (!book) {
            alert('书籍不存在');
            return;
        }
        
        // 填充表单
        document.getElementById('editBookId').value = book.id;
        document.getElementById('editBookTitle').value = book.title || '';
        document.getElementById('editBookAuthor').value = book.author || '';
        document.getElementById('editBookCategory').value = book.category || 'other';
        document.getElementById('editBookPrice').value = book.price || 0;
        document.getElementById('editBookDescription').value = book.description || book.desc || '';
        document.getElementById('editBookStatus').value = book.status || 'available';
        
        // 显示模态框
        document.getElementById('edit-book-modal').classList.add('active');
    } catch (error) {
        console.error('编辑书籍失败:', error);
        alert('获取书籍详情失败，请稍后重试');
    }
};

/**
 * 删除书籍
 */
window.deleteBook = function(id) {
    const modal = document.getElementById('delete-book-modal');
    const message = document.getElementById('deleteBookMessage');
    
    // 存储要删除的书籍ID
    modal.dataset.bookId = id;
    message.textContent = '确定要删除这本书籍吗？此操作不可撤销。';
    
    modal.classList.add('active');
};

/**
 * 确认删除书籍
 */
async function confirmDeleteBook() {
    const modal = document.getElementById('delete-book-modal');
    const bookId = modal.dataset.bookId;
    
    if (!bookId) {
        return;
    }
    
    try {
        const response = await fetch(`/api/books/${bookId}`, {
            method: 'DELETE',
            credentials: 'include'
        });
        
        const result = await response.json();
        
        if (result.status === 'success') {
            if (typeof showToast === 'function') {
                showToast('书籍删除成功', 'success');
            } else {
                alert('书籍删除成功');
            }
            closeModal('delete-book-modal');
            filterBooks(); // 重新加载书籍列表
        } else {
            alert('删除失败：' + (result.message || '未知错误'));
        }
    } catch (error) {
        console.error('删除书籍失败:', error);
        alert('删除书籍时发生错误，请稍后重试');
    }
}

/**
 * 编辑分类
 */
window.editCategory = function(id) {
    console.log('编辑分类:', id);
    showToast('编辑分类功能开发中', 'info');
};

/**
 * 删除分类
 */
window.deleteCategory = function(id) {
    if (confirm('确定要删除该分类吗？')) {
        console.log('删除分类:', id);
        showToast('分类删除成功', 'success');
        initCategoriesTable(); // 重新加载分类列表
    }
};

/**
 * 初始化admin.html页面
 */
async function initAdminPage() {
    // 初始化侧边栏切换
    initSidebarToggle();
    
    // 初始化区域导航
    initSectionNavigation();
    
    // 初始化仪表盘
    initDashboardStats();
    initCharts();
    
    // 初始化搜索和过滤
    initSearchAndFilter();
    
    // 初始化模态框
    initModals();
    
    // 初始化系统设置
    initSystemSettings();
    
    // 初始化书籍列表
    await filterBooks();
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    initAdminPage();
});

// 重新导出函数
// 移除export语句，确保浏览器兼容性