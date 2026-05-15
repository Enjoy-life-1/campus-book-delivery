// 账户设置页面JavaScript模块

/**
 * 保存头像到用户信息
 * @param {string} avatarUrl - 头像图片的Data URL
 * @returns {Promise} 返回Promise以便链式调用
 */
async function saveAvatar(avatarUrl) {
    try {
        const response = await fetch('/api/user/info', {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            credentials: 'include',
            body: JSON.stringify({
                avatar: avatarUrl
            })
        });
        
        const result = await response.json();
        
        if (result.status === 'success') {
            // 更新本地用户信息
            if (typeof getCurrentUser === 'function') {
                const user = getCurrentUser();
                if (user) {
                    user.avatar = avatarUrl;
                    if (typeof saveUser === 'function') {
                        saveUser(user);
                    }
                }
            }
            showAlert();
            return Promise.resolve();
        } else {
            alert('保存头像失败：' + (result.message || '未知错误'));
            return Promise.reject(new Error(result.message || '保存失败'));
        }
    } catch (error) {
        console.error('保存头像失败:', error);
        alert('保存头像时发生错误，请稍后重试');
        return Promise.reject(error);
    }
}

/**
 * 保存个人信息
 */
async function saveProfile() {
    const username = document.getElementById('usernameInput').value.trim();
    const school = document.getElementById('schoolInput').value.trim();
    const introduction = document.getElementById('introductionInput').value.trim();
    
    // 验证用户名
    if (!username) {
        alert('请输入用户名');
        return;
    }
    
    try {
        const response = await fetch('/api/user/info', {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            credentials: 'include',
            body: JSON.stringify({
                username: username,
                school: school,
                introduction: introduction
            })
        });
        
        const result = await response.json();
        
        if (result.status === 'success') {
            // 更新本地用户信息
            if (typeof getCurrentUser === 'function') {
                const user = getCurrentUser();
                if (user) {
                    user.username = username;
                    user.school = school;
                    user.introduction = introduction;
                    if (typeof saveUser === 'function') {
                        saveUser(user);
                    }
                }
            }
            
            // 更新显示的用户名
            const usernameElement = document.getElementById('username');
            if (usernameElement) {
                usernameElement.textContent = username;
            }
            
            // 更新用户菜单
            if (typeof updateUserMenu === 'function') {
                updateUserMenu();
            }
            
            showAlert();
        } else {
            alert('保存失败：' + (result.message || '未知错误'));
        }
    } catch (error) {
        console.error('保存个人信息失败:', error);
        alert('保存时发生错误，请稍后重试');
    }
}

/**
 * 修改用户密码
 */
async function changePassword() {
    const oldPassword = document.getElementById('oldPassword').value;
    const newPassword = document.getElementById('newPassword').value;
    const confirmPassword = document.getElementById('confirmPassword').value;
    
    // 验证密码
    if (!oldPassword || !newPassword || !confirmPassword) {
        alert('请填写所有密码字段');
        return;
    }
    
    if (newPassword !== confirmPassword) {
        alert('两次输入的新密码不一致');
        return;
    }
    
    if (newPassword.length < 6) {
        alert('密码长度不能少于6位');
        return;
    }
    
    try {
        const response = await fetch('/api/user/password', {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            credentials: 'include',
            body: JSON.stringify({
                oldPassword: oldPassword,
                newPassword: newPassword,
                confirmPassword: confirmPassword
            })
        });
        
        const result = await response.json();
        
        if (result.status === 'success') {
            // 清空表单
            document.getElementById('securityForm').reset();
            
            showAlert();
            alert('密码修改成功，请重新登录');
            
            // 退出登录
            if (typeof logout === 'function') {
                logout();
            } else {
                // 如果没有logout函数，手动清除session并跳转
                fetch('/api/logout', {
                    method: 'POST',
                    credentials: 'include'
                }).then(() => {
                    localStorage.removeItem('currentUser');
                    window.location.href = '/login';
                });
            }
        } else {
            alert('修改密码失败：' + (result.message || '未知错误'));
        }
    } catch (error) {
        console.error('修改密码失败:', error);
        alert('修改密码时发生错误，请稍后重试');
    }
}

/**
 * 显示保存成功提示
 */
function showAlert() {
    const alert = document.getElementById('saveAlert');
    if (alert) {
        alert.style.display = 'block';
        
        // 3秒后隐藏提示
        setTimeout(() => {
            alert.style.display = 'none';
        }, 3000);
    }
}

/**
 * 加载用户信息
 */
async function loadUserInfo() {
    try {
        const response = await fetch('/api/user/info', {
            credentials: 'include'
        });
        
        if (!response.ok) {
            if (response.status === 401) {
                window.location.href = '/login?redirect=/accountSettings';
                return;
            }
            throw new Error('获取用户信息失败');
        }
        
        const result = await response.json();
        
        if (result.status === 'success' && result.user) {
            const user = result.user;
            
            // 填充表单数据
            const usernameElement = document.getElementById('username');
            if (usernameElement) {
                usernameElement.textContent = user.username || '我的账户';
            }
            
            document.getElementById('usernameInput').value = user.username || '';
            document.getElementById('phoneInput').value = user.phone || '';
            document.getElementById('schoolInput').value = user.school || '';
            document.getElementById('introductionInput').value = user.introduction || '';
            
            // 设置头像
            if (user.avatar) {
                document.getElementById('avatarImg').src = user.avatar;
            }
            
            // 更新本地用户信息
            if (typeof saveUser === 'function') {
                saveUser(user);
            }
        }
    } catch (error) {
        console.error('加载用户信息失败:', error);
    }
}

/**
 * 初始化页面事件监听器和数据
 */
function initAccountSettings() {
    // 确保common.js已加载
    if (typeof checkLogin !== 'function') {
        console.error('checkLogin函数未定义，请确保common.js已加载');
        return;
    }
    
    // 检查登录状态
    if (!checkLogin('/accountSettings')) {
        return;
    }
    
    // 加载用户信息
    loadUserInfo();
    
    // 头像上传功能
    const changeAvatarBtn = document.getElementById('changeAvatarBtn');
    const avatarInput = document.getElementById('avatarInput');
    
    if (changeAvatarBtn && avatarInput) {
        changeAvatarBtn.addEventListener('click', function() {
            avatarInput.click();
        });
        
        avatarInput.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (file) {
                // 验证文件类型
                if (!file.type.startsWith('image/')) {
                    alert('请选择图片文件');
                    return;
                }
                
                // 验证文件大小（限制为2MB）
                if (file.size > 2 * 1024 * 1024) {
                    alert('图片大小不能超过2MB');
                    return;
                }
                
                const reader = new FileReader();
                reader.onload = function(event) {
                    document.getElementById('avatarImg').src = event.target.result;
                    // 保存头像地址到用户信息
                    saveAvatar(event.target.result).then(() => {
                        // 触发自定义事件，通知其他页面更新头像
                        window.dispatchEvent(new CustomEvent('avatarUpdated', {
                            detail: { avatarUrl: event.target.result }
                        }));
                        // 触发storage事件，确保其他页面也能收到更新
                        localStorage.setItem('avatarUpdated', Date.now().toString());
                    });
                };
                reader.readAsDataURL(file);
            }
        });
    }
    
    // 保存个人信息
    const profileForm = document.getElementById('profileForm');
    if (profileForm) {
        profileForm.addEventListener('submit', function(e) {
            e.preventDefault();
            saveProfile();
        });
    }
    
    // 修改密码
    const securityForm = document.getElementById('securityForm');
    if (securityForm) {
        securityForm.addEventListener('submit', function(e) {
            e.preventDefault();
            changePassword();
        });
    }
    
    // 退出登录
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', function(e) {
            e.preventDefault();
            if (typeof logout === 'function') {
                logout();
            } else {
                fetch('/api/logout', {
                    method: 'POST',
                    credentials: 'include'
                }).then(() => {
                    localStorage.removeItem('currentUser');
                    window.location.href = '/login';
                });
            }
        });
    }
    
    const logoutBtnMenu = document.getElementById('logoutBtnMenu');
    if (logoutBtnMenu) {
        logoutBtnMenu.addEventListener('click', function(e) {
            e.preventDefault();
            if (typeof logout === 'function') {
                logout();
            } else {
                fetch('/api/logout', {
                    method: 'POST',
                    credentials: 'include'
                }).then(() => {
                    localStorage.removeItem('currentUser');
                    window.location.href = '/login';
                });
            }
        });
    }
}

// 页面加载时初始化
if (typeof window !== 'undefined') {
    document.addEventListener('DOMContentLoaded', initAccountSettings);
}
