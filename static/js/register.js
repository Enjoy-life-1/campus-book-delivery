// register.js - 注册页面功能实现
// 使用common.js中定义的apiRequest函数代替import语句

// 基本UI工具函数
function showToast(message, type = 'info') {
    // 移除之前的toast
    const existingToasts = document.querySelectorAll('.toast-message');
    existingToasts.forEach(toast => toast.remove());
    
    const toast = document.createElement('div');
    toast.className = `toast-message toast-${type}`;
    toast.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 9999;
        min-width: 300px;
        max-width: 400px;
        padding: 16px 20px;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        animation: slideIn 0.3s ease-out;
        display: flex;
        align-items: center;
        gap: 12px;
    `;
    
    // 根据类型设置颜色
    const colors = {
        success: { bg: '#4CAF50', icon: '✓' },
        error: { bg: '#f44336', icon: '✗' },
        info: { bg: '#2196F3', icon: 'ℹ' },
        warning: { bg: '#ff9800', icon: '⚠' }
    };
    
    const color = colors[type] || colors.info;
    toast.style.backgroundColor = color.bg;
    toast.style.color = 'white';
    
    toast.innerHTML = `
        <span style="font-size: 20px; font-weight: bold;">${color.icon}</span>
        <span style="flex: 1; font-size: 14px; line-height: 1.5;">${message}</span>
    `;
    
    document.body.appendChild(toast);
    
    // 添加动画样式
    if (!document.getElementById('toast-animations')) {
        const style = document.createElement('style');
        style.id = 'toast-animations';
        style.textContent = `
            @keyframes slideIn {
                from {
                    transform: translateX(100%);
                    opacity: 0;
                }
                to {
                    transform: translateX(0);
                    opacity: 1;
                }
            }
        `;
        document.head.appendChild(style);
    }
    
    setTimeout(() => {
        toast.style.animation = 'slideIn 0.3s ease-out reverse';
        setTimeout(() => {
            toast.remove();
        }, 300);
    }, 3000);
}

function showLoading(message = '加载中...') {
    // 先移除可能存在的loading
    hideLoading();
    const loading = document.createElement('div');
    loading.className = 'loading-indicator d-flex justify-content-center align-items-center fixed inset-0 bg-black bg-opacity-50';
    loading.style.zIndex = '9999';
    loading.innerHTML = `<div class="d-flex flex-column align-items-center">
        <div class="spinner-border text-white mb-2" role="status"></div>
        <div class="text-white">${message}</div>
    </div>`;
    document.body.appendChild(loading);
}

function hideLoading() {
    const loading = document.querySelector('.loading-indicator');
    if (loading) loading.remove();
}

function showValidationError(inputId, message) {
    const input = document.getElementById(inputId);
    if (!input) return;
    
    // 添加错误样式
    input.classList.add('is-invalid');
    
    // 创建或更新错误提示元素
    let errorElement = input.parentElement.querySelector('.invalid-feedback');
    if (!errorElement) {
        errorElement = document.createElement('div');
        errorElement.className = 'invalid-feedback';
        input.parentElement.appendChild(errorElement);
    }
    
    errorElement.textContent = message;
    errorElement.style.display = 'block';
}

function clearValidationError(inputId) {
    const input = document.getElementById(inputId);
    if (!input) return;
    
    input.classList.remove('is-invalid');
    
    const errorElement = input.parentElement.querySelector('.invalid-feedback');
    if (errorElement) {
        errorElement.style.display = 'none';
    }
}

// 实时验证函数
function validateField(inputId, validator, errorMessage) {
    const input = document.getElementById(inputId);
    if (!input) return false;
    
    const value = input.value.trim();
    const isValid = validator(value);
    
    if (!isValid) {
        showValidationError(inputId, errorMessage);
        return false;
    } else {
        clearValidationError(inputId);
        return true;
    }
}

/**
 * 发送验证码
 * @param {string} phone - 手机号码
 * @returns {Promise<boolean>}
 */
async function sendVerificationCode(phone) {
    try {
        showLoading('发送中...');
        const response = await apiRequest('/send_code', {
            method: 'POST',
            body: JSON.stringify({ phone })
        });
        hideLoading();
        
        if (response.success || response.status === 'success') {
            // 显示测试验证码提示
            const testCode = response.code || '666666';
            showToast(`验证码已发送（测试验证码：${testCode}）`, 'success');
            startCountdown();
            return true;
        } else {
            showToast(response.message || '发送失败，请稍后重试', 'error');
            return false;
        }
    } catch (error) {
        hideLoading();
        showToast(error.message || '网络错误，请稍后重试', 'error');
        return false;
    }
}

/**
 * 开始倒计时
 */
function startCountdown() {
    const sendBtn = document.getElementById('sendCodeBtn');
    let countdown = 60;
    sendBtn.disabled = true;
    sendBtn.textContent = `${countdown}秒后重试`;
    
    const timer = setInterval(() => {
        countdown--;
        sendBtn.textContent = `${countdown}秒后重试`;
        
        if (countdown <= 0) {
            clearInterval(timer);
            sendBtn.disabled = false;
            sendBtn.textContent = '获取验证码';
        }
    }, 1000);
}

/**
 * 注册用户
 * @param {Object} userData - 用户数据
 * @returns {Promise<boolean>}
 */
async function registerUser(userData) {
    try {
        showLoading('注册中...');
        const response = await apiRequest('/register', {
            method: 'POST',
            body: JSON.stringify(userData)
        });
        hideLoading();
        
        if (response.status === 'success') {
            showToast('注册成功！即将跳转到登录页', 'success');
            setTimeout(() => {
                window.location.href = '/login';
            }, 1500);
            return true;
        } else {
            // 根据错误类型显示不同的提示
            const errorMsg = response.message || '注册失败，请稍后重试';
            showToast(errorMsg, 'error');
            
            // 如果是用户名或手机号已存在的错误，高亮对应字段
            if (errorMsg.includes('用户名')) {
                showValidationError('username', errorMsg);
            } else if (errorMsg.includes('手机号')) {
                showValidationError('phone', errorMsg);
            } else if (errorMsg.includes('验证码')) {
                showValidationError('verifyCode', errorMsg);
            }
            
            return false;
        }
    } catch (error) {
        hideLoading();
        // 处理网络错误或服务器错误
        let errorMsg = '网络错误，请稍后重试';
        if (error.message) {
            errorMsg = error.message;
        } else if (error.response && error.response.message) {
            errorMsg = error.response.message;
        }
        showToast(errorMsg, 'error');
        return false;
    }
}

/**
 * 验证密码强度
 * @param {string} password - 密码
 * @returns {number} 强度评分(0-5)
 */
function calculatePasswordStrength(password) {
    let strength = 0;
    
    // 长度检查
    if (password.length >= 8) strength++;
    if (password.length >= 12) strength++;
    
    // 复杂度检查
    if (/[A-Z]/.test(password)) strength++;
    if (/[a-z]/.test(password)) strength++;
    if (/[0-9]/.test(password)) strength++;
    if (/[^A-Za-z0-9]/.test(password)) strength++;
    
    return strength;
}

/**
 * 初始化密码强度检测器
 */
function initPasswordStrengthChecker() {
    const passwordInput = document.getElementById('password');
    const strengthBar = document.getElementById('strengthBar');
    const strengthText = document.getElementById('strengthText');
    
    if (passwordInput && strengthBar && strengthText) {
        passwordInput.addEventListener('input', () => {
            const password = passwordInput.value;
            const strength = calculatePasswordStrength(password);
            
            // 更新强度显示
            strengthBar.style.width = `${strength * 20}%`;
            
            switch(strength) {
                case 0:
                case 1:
                    strengthBar.className = 'strength-bar bg-danger';
                    strengthText.textContent = '弱：建议增加密码长度和复杂度';
                    break;
                case 2:
                case 3:
                    strengthBar.className = 'strength-bar bg-warning';
                    strengthText.textContent = '中：可以再加入特殊字符';
                    break;
                case 4:
                case 5:
                    strengthBar.className = 'strength-bar bg-success';
                    strengthText.textContent = '强：密码很安全';
                    break;
            }
        });
    }
}

/**
 * 初始化实时验证
 */
function initRealTimeValidation() {
    // 用户名验证
    const usernameInput = document.getElementById('username');
    if (usernameInput) {
        usernameInput.addEventListener('blur', () => {
            validateField('username', 
                (value) => value.length > 0,
                '请输入用户名'
            );
        });
    }
    
    // 手机号验证
    const phoneInput = document.getElementById('phone');
    if (phoneInput) {
        phoneInput.addEventListener('blur', () => {
            validateField('phone',
                (value) => /^1[3-9]\d{9}$/.test(value),
                '请输入有效的11位手机号码'
            );
        });
    }
    
    // 验证码验证
    const verifyCodeInput = document.getElementById('verifyCode');
    if (verifyCodeInput) {
        verifyCodeInput.addEventListener('blur', () => {
            validateField('verifyCode',
                (value) => /^\d{6}$/.test(value),
                '请输入6位数字验证码'
            );
        });
    }
    
    // 密码验证
    const passwordInput = document.getElementById('password');
    if (passwordInput) {
        passwordInput.addEventListener('blur', () => {
            validateField('password',
                (value) => value.length >= 6,
                '密码长度不能少于6位'
            );
        });
    }
}

/**
 * 初始化表单验证
 */
function initFormValidation() {
    const form = document.getElementById('registerForm');
    
    if (form) {
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            // 获取表单数据
            const userData = {
                username: document.getElementById('username').value.trim(),
                phone: document.getElementById('phone').value.trim(),
                password: document.getElementById('password').value.trim(),
                verifyCode: document.getElementById('verifyCode').value.trim()
            };

            // 清除所有验证错误
            clearValidationError('username');
            clearValidationError('phone');
            clearValidationError('verifyCode');
            clearValidationError('password');

            // 表单验证
            let isValid = true;
            
            // 验证用户名
            if (!userData.username || userData.username.trim().length === 0) {
                showValidationError('username', '请输入用户名');
                isValid = false;
            }
            
            // 验证手机号
            if (!/^1[3-9]\d{9}$/.test(userData.phone)) {
                showValidationError('phone', '请输入有效的11位手机号码');
                isValid = false;
            }
            
            // 验证验证码
            if (!/^\d{6}$/.test(userData.verifyCode)) {
                showValidationError('verifyCode', '请输入6位数字验证码');
                isValid = false;
            }
            
            // 验证密码
            if (!userData.password || userData.password.length < 6) {
                showValidationError('password', '密码长度不能少于6位');
                isValid = false;
            }

            // 如果验证失败，显示提示
            if (!isValid) {
                showToast('请检查并修正表单错误', 'error');
                return;
            }

            // 如果验证通过，调用注册函数
            await registerUser(userData);
        });
    }
}

/**
 * 初始化验证码按钮
 */
function initVerificationCodeButton() {
    const sendBtn = document.getElementById('sendCodeBtn');
    
    if (sendBtn) {
        sendBtn.addEventListener('click', async () => {
            const phoneInput = document.getElementById('phone');
            const phone = phoneInput.value.trim();
            
            if (!/^1[3-9]\d{9}$/.test(phone)) {
                showToast('请输入有效的手机号码', 'error');
                return;
            }
            
            await sendVerificationCode(phone);
        });
    }
}

/**
 * 初始化密码显示切换
 */
function initPasswordToggle() {
    const passwordToggle = document.querySelector('.password-toggle');
    const passwordInput = document.getElementById('password');
    
    if (passwordToggle && passwordInput) {
        passwordToggle.addEventListener('click', () => {
            const type = passwordInput.getAttribute('type') === 'password' ? 'text' : 'password';
            passwordInput.setAttribute('type', type);
            
            // 切换图标
            const icon = passwordToggle.querySelector('i');
            if (icon) {
                icon.className = type === 'password' ? 'fa fa-eye' : 'fa fa-eye-slash';
            }
        });
    }
}

/**
 * 页面初始化
 */
function initRegisterPage() {
    // 初始化各个功能模块
    initPasswordStrengthChecker();
    initRealTimeValidation();
    initFormValidation();
    initVerificationCodeButton();
    initPasswordToggle();
    
    console.log('注册页面初始化完成');
}

// 页面加载完成后初始化
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initRegisterPage);
} else {
    initRegisterPage();
}