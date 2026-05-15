// main.js - 校园书递项目全局初始化和事件处理

// 页面加载完成后的初始化
window.addEventListener('DOMContentLoaded', function() {
    // 更新导航栏用户状态
    if (typeof updateNavbarUserStatus === 'function') {
        updateNavbarUserStatus();
    }
    
    // 初始化登出按钮事件
    initLogoutButton();
    
    // 监听storage事件，当其他页面修改localStorage时更新当前页面
    window.addEventListener('storage', function() {
        if (typeof updateNavbarUserStatus === 'function') {
            updateNavbarUserStatus();
        }
    });
    
    // 初始化页面特定功能
    initPageSpecificFeatures();
});

// 初始化登出按钮
function initLogoutButton() {
    const logoutButton = document.getElementById('logout-btn');
    if (logoutButton) {
        logoutButton.addEventListener('click', async function(event) {
            event.preventDefault();
            if (confirm('确定要退出登录吗？')) {
                if (typeof logout === 'function') {
                    await logout();
                }
            }
        });
    }
}

// 初始化页面特定功能
function initPageSpecificFeatures() {
    // 根据当前页面URL执行不同的初始化
    const pathname = window.location.pathname;
    
    // 示例：为不同页面添加特定的初始化逻辑
    switch(pathname) {
        case '/':
        case '/index.html':
            initHomePage();
            break;
        case '/booksList':
        case '/booksList.html':
            initBooksListPage();
            break;
        case '/login':
        case '/login.html':
            initLoginPage();
            break;
        // 可以根据需要添加更多页面的初始化
        default:
            // 通用初始化逻辑
            break;
    }
}

// 首页初始化
function initHomePage() {
    // 首页特定的初始化代码
    console.log('初始化首页...');
    
    // 示例：加载推荐书籍
    if (typeof loadRecommendedBooks === 'function') {
        loadRecommendedBooks();
    }
}

// 书籍列表页初始化
function initBooksListPage() {
    // 书籍列表页特定的初始化代码
    console.log('初始化书籍列表页...');
    
    // 示例：加载书籍列表
    if (typeof loadBooksList === 'function') {
        loadBooksList();
    }
}

// 登录页初始化
function initLoginPage() {
    // 登录页特定的初始化代码
    console.log('初始化登录页...');
    
    // 自动聚焦到用户名输入框
    const usernameInput = document.getElementById('username');
    if (usernameInput) {
        usernameInput.focus();
    }
}

// 显示加载状态
function showLoading(elementId, message = '加载中...') {
    const element = document.getElementById(elementId);
    if (element) {
        element.innerHTML = `<div class="text-center py-4"><div class="spinner-border" role="status"><span class="visually-hidden">${message}</span></div><p class="mt-2">${message}</p></div>`;
    }
}

// 显示错误信息
function showError(elementId, message = '操作失败，请重试') {
    const element = document.getElementById(elementId);
    if (element) {
        element.innerHTML = `<div class="alert alert-danger" role="alert">${message}</div>`;
    }
}

// 显示成功信息
function showSuccess(elementId, message = '操作成功') {
    const element = document.getElementById(elementId);
    if (element) {
        element.innerHTML = `<div class="alert alert-success" role="alert">${message}</div>`;
    }
}

// 显示提示消息
function showToast(message, type = 'info') {
    // 创建toast元素
    const toastId = `toast-${Date.now()}`;
    const toastHtml = `
    <div id="${toastId}" class="toast position-fixed bottom-4 right-4 bg-${type === 'error' ? 'danger' : type === 'success' ? 'success' : 'secondary'} text-white" role="alert" aria-live="assertive" aria-atomic="true">
        <div class="toast-body">
            ${message}
        </div>
    </div>
    `;
    
    // 添加到body
    document.body.insertAdjacentHTML('beforeend', toastHtml);
    
    // 显示toast
    const toast = new bootstrap.Toast(document.getElementById(toastId));
    toast.show();
    
    // 3秒后自动移除
    setTimeout(() => {
        const element = document.getElementById(toastId);
        if (element) {
            element.remove();
        }
    }, 3000);
}

// 表单验证辅助函数
function validateForm(formId, rules) {
    const form = document.getElementById(formId);
    if (!form) return false;
    
    let isValid = true;
    
    // 清除所有错误提示
    document.querySelectorAll('.form-error').forEach(el => el.remove());
    
    // 验证每个字段
    Object.entries(rules).forEach(([fieldName, fieldRules]) => {
        const field = form.querySelector(`[name="${fieldName}"]`);
        if (!field) return;
        
        const value = field.value.trim();
        
        // 必填验证
        if (fieldRules.required && !value) {
            showFieldError(field, fieldRules.message || '此字段为必填项');
            isValid = false;
            return;
        }
        
        // 最小长度验证
        if (fieldRules.minLength && value.length < fieldRules.minLength) {
            showFieldError(field, fieldRules.minLengthMessage || `长度不能少于${fieldRules.minLength}个字符`);
            isValid = false;
            return;
        }
        
        // 正则表达式验证
        if (fieldRules.pattern && !fieldRules.pattern.test(value)) {
            showFieldError(field, fieldRules.patternMessage || '格式不正确');
            isValid = false;
            return;
        }
    });
    
    return isValid;
}

// 显示字段错误
function showFieldError(field, message) {
    // 移除已存在的错误提示
    const existingError = field.parentNode.querySelector('.form-error');
    if (existingError) {
        existingError.remove();
    }
    
    // 添加新的错误提示
    const errorElement = document.createElement('div');
    errorElement.className = 'form-error text-danger text-sm mt-1';
    errorElement.textContent = message;
    field.parentNode.appendChild(errorElement);
    
    // 高亮错误字段
    field.classList.add('is-invalid');
    
    // 聚焦到错误字段
    field.focus();
    
    // 输入时清除错误
    field.addEventListener('input', function handler() {
        field.classList.remove('is-invalid');
        errorElement.remove();
        field.removeEventListener('input', handler);
    });
}

// 添加全局扩展错误处理
(function() {
    // 全局runtime错误处理
    const originalRuntimeErrorHandler = window.onerror;
    window.onerror = function(message, source, lineno, colno, error) {
        // 忽略浏览器扩展与开发工具相关的错误
        if (message && message.includes('Unchecked runtime.lastError') && 
            message.includes('can not use with devtools')) {
            console.warn('忽略浏览器扩展开发工具错误:', message);
            return true; // 阻止默认错误处理
        }
        
        // 调用原始错误处理器（如果存在）
        if (originalRuntimeErrorHandler) {
            return originalRuntimeErrorHandler(message, source, lineno, colno, error);
        }
        
        return false;
    };
    
    // 捕获Promise未处理的拒绝
    window.addEventListener('unhandledrejection', function(event) {
        if (event.reason && typeof event.reason === 'string' &&
            event.reason.includes('Unchecked runtime.lastError') &&
            event.reason.includes('can not use with devtools')) {
            console.warn('忽略Promise中浏览器扩展开发工具错误:', event.reason);
            event.preventDefault();
        }
    });
    
    // 安全包装Chrome扩展API
    if (window.chrome && window.chrome.runtime) {
        // 存储原始方法
        const originalMethods = {
            sendMessage: chrome.runtime.sendMessage,
            connect: chrome.runtime.connect,
            getURL: chrome.runtime.getURL,
            getManifest: chrome.runtime.getManifest
        };
        
        // 安全包装sendMessage
        chrome.runtime.sendMessage = function(message, options, callback) {
            try {
                if (typeof options === 'function') {
                    callback = options;
                    options = undefined;
                }
                
                const safeCallback = function(response) {
                    try {
                        if (callback) callback(response);
                    } catch (e) {
                        if (!e.message || !e.message.includes('can not use with devtools')) {
                            console.error('Chrome扩展回调错误:', e);
                        }
                    }
                };
                
                if (options) {
                    return originalMethods.sendMessage.call(this, message, options, safeCallback);
                } else {
                    return originalMethods.sendMessage.call(this, message, safeCallback);
                }
            } catch (e) {
                if (!e.message || !e.message.includes('can not use with devtools')) {
                    console.error('Chrome扩展sendMessage错误:', e);
                }
                return null;
            }
        };
        
        // 安全包装其他可能使用的方法
        ['connect', 'getURL', 'getManifest'].forEach(method => {
            chrome.runtime[method] = function() {
                try {
                    return originalMethods[method].apply(this, arguments);
                } catch (e) {
                    if (!e.message || !e.message.includes('can not use with devtools')) {
                        console.error(`Chrome扩展${method}错误:`, e);
                    }
                    return method === 'getURL' ? arguments[0] : null;
                }
            };
        });
    }
})();