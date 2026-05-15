// 全局JavaScript文件 - 校园书递管理系统

// 全局变量定义
window.CampusBooks = window.CampusBooks || {};

// 工具函数集合
CampusBooks.utils = {
    // 显示通知消息
    showNotification: function(message, type = 'info') {
        // 简单的通知实现，后续可以集成更复杂的通知库
        console.log(`[${type.toUpperCase()}] ${message}`);
        
        // 如果页面中有toast容器，可以在这里实现DOM通知
        const toastContainer = document.getElementById('toast-container');
        if (toastContainer) {
            const toast = document.createElement('div');
            toast.className = `toast alert alert-${type} fade show`;
            toast.innerHTML = `
                <div class="toast-header">
                    <strong class="mr-auto">通知</strong>
                    <button type="button" class="ml-2 mb-1 close" data-dismiss="toast">&times;</button>
                </div>
                <div class="toast-body">${message}</div>
            `;
            toastContainer.appendChild(toast);
            
            // 3秒后自动关闭
            setTimeout(() => {
                toast.classList.remove('show');
                toast.classList.add('hide');
                setTimeout(() => toast.remove(), 500);
            }, 3000);
        }
    },
    
    // 格式化日期
    formatDate: function(date) {
        const d = new Date(date);
        const year = d.getFullYear();
        const month = String(d.getMonth() + 1).padStart(2, '0');
        const day = String(d.getDate()).padStart(2, '0');
        return `${year}-${month}-${day}`;
    },
    
    // 格式化金额
    formatCurrency: function(amount) {
        return `¥${parseFloat(amount).toFixed(2)}`;
    },
    
    // 获取URL参数
    getUrlParams: function() {
        const params = {};
        const queryString = window.location.search.substring(1);
        const pairs = queryString.split('&');
        
        for (let i = 0; i < pairs.length; i++) {
            const pair = pairs[i].split('=');
            params[decodeURIComponent(pair[0])] = decodeURIComponent(pair[1] || '');
        }
        
        return params;
    },
    
    // 深拷贝对象
    deepClone: function(obj) {
        return JSON.parse(JSON.stringify(obj));
    },
    
    // 验证邮箱格式
    isValidEmail: function(email) {
        const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return re.test(email);
    },
    
    // 验证手机号格式（中国大陆）
    isValidPhone: function(phone) {
        const re = /^1[3-9]\d{9}$/;
        return re.test(phone);
    },
    
    // 防抖函数
    debounce: function(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },
    
    // 节流函数
    throttle: function(func, limit) {
        let inThrottle;
        return function(...args) {
            if (!inThrottle) {
                func.apply(this, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    }
};

// API请求封装
CampusBooks.api = {
    baseUrl: '/api',
    
    // 通用请求方法
    request: function(endpoint, method = 'GET', data = null, headers = {}) {
        return new Promise((resolve, reject) => {
            const xhr = new XMLHttpRequest();
            const url = `${this.baseUrl}${endpoint}`;
            
            xhr.open(method, url, true);
            
            // 设置默认请求头
            xhr.setRequestHeader('Content-Type', 'application/json');
            
            // 设置自定义请求头
            for (const [key, value] of Object.entries(headers)) {
                xhr.setRequestHeader(key, value);
            }
            
            xhr.onload = function() {
                if (xhr.status >= 200 && xhr.status < 300) {
                    try {
                        const response = JSON.parse(xhr.responseText);
                        resolve(response);
                    } catch (e) {
                        resolve(xhr.responseText);
                    }
                } else {
                    reject(new Error(`请求失败: ${xhr.status} ${xhr.statusText}`));
                }
            };
            
            xhr.onerror = function() {
                reject(new Error('网络错误'));
            };
            
            if (data && (method === 'POST' || method === 'PUT' || method === 'PATCH')) {
                xhr.send(JSON.stringify(data));
            } else {
                xhr.send();
            }
        });
    },
    
    // 快捷方法
    get: function(endpoint, headers = {}) {
        return this.request(endpoint, 'GET', null, headers);
    },
    
    post: function(endpoint, data = {}, headers = {}) {
        return this.request(endpoint, 'POST', data, headers);
    },
    
    put: function(endpoint, data = {}, headers = {}) {
        return this.request(endpoint, 'PUT', data, headers);
    },
    
    delete: function(endpoint, headers = {}) {
        return this.request(endpoint, 'DELETE', null, headers);
    }
};

// DOM加载完成后执行的初始化函数
CampusBooks.init = function() {
    console.log('CampusBooks 全局初始化完成');
    
    // 初始化所有工具提示
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-toggle="tooltip"]'));
    if (window.bootstrap && window.bootstrap.Tooltip) {
        tooltipTriggerList.forEach(tooltipTriggerEl => {
            new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }
    
    // 初始化所有弹窗
    const modalTriggerList = [].slice.call(document.querySelectorAll('[data-toggle="modal"]'));
    if (window.bootstrap && window.bootstrap.Modal) {
        modalTriggerList.forEach(modalTriggerEl => {
            new bootstrap.Modal(modalTriggerEl);
        });
    }
};

// 监听DOM加载完成事件
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', CampusBooks.init);
} else {
    CampusBooks.init();
}

// 导出到全局作用域
window.utils = CampusBooks.utils;
window.api = CampusBooks.api;