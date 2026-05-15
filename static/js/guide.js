// 登录状态同步函数（与其他页面保持一致）
function updateUserMenu() {
    const user = localStorage.getItem('currentUser');
    const userMenu = document.getElementById('userMenu');
    
    if (user) {
        const userObj = JSON.parse(user);
        userMenu.innerHTML = `
            <a class="nav-link dropdown-toggle" href="#" role="button" data-bs-toggle="dropdown">
                <i class="fa fa-user-circle text-primary"></i> ${userObj.user?.username || userObj.username || '用户'}
            </a>
            <ul class="dropdown-menu dropdown-menu-end">
                <li><a class="dropdown-item" href="/personalCenter">个人中心</a></li>
                <li><a class="dropdown-item" href="/myBooks">我的书籍</a></li>
                <li><hr class="dropdown-divider"></li>
                <li><a class="dropdown-item" href="#" onclick="logout()">退出登录</a></li>
            </ul>
        `;
    } else {
        userMenu.innerHTML = `
            <a class="nav-link dropdown-toggle" href="#" role="button" data-bs-toggle="dropdown">
                <i class="fa fa-user text-primary"></i> 登录/注册
            </a>
            <ul class="dropdown-menu dropdown-menu-end">
                <li><a class="dropdown-item" href="/login">登录</a></li>
                <li><a class="dropdown-item" href="/register">注册</a></li>
            </ul>
        `;
    }
}

// 退出登录函数
function logout() {
    localStorage.removeItem('currentUser');
    window.location.reload();
}

// 滚动到指定区域
function scrollToSection(sectionId) {
    const section = document.getElementById(sectionId);
    if (section) {
        const card = section.closest('.guide-card');
        if (card) {
            // 展开卡片
            if (!card.classList.contains('active')) {
                card.classList.add('active');
            }
            // 滚动到卡片位置
            setTimeout(() => {
                card.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }, 100);
        }
    }
}

// 切换卡片展开/收起
function toggleCard(header) {
    const card = header.closest('.collapsible-card');
    const isActive = card.classList.contains('active');
    
    // 关闭所有其他卡片（可选，如果想要手风琴效果）
    // document.querySelectorAll('.collapsible-card').forEach(c => {
    //     if (c !== card) {
    //         c.classList.remove('active');
    //     }
    // });
    
    // 切换当前卡片
    if (isActive) {
        card.classList.remove('active');
    } else {
        card.classList.add('active');
    }
}

// 步骤项点击展开详情（可选功能）
function toggleStepDetail(stepItem) {
    const detail = stepItem.querySelector('.step-detail');
    if (detail) {
        detail.classList.toggle('expanded');
    }
}

// 页面加载初始化
window.onload = function() {
    updateUserMenu();
    
    // 监听localStorage变化
    window.addEventListener('storage', function(e) {
        if (e.key === 'currentUser') {
            updateUserMenu();
        }
    });
    
    // 默认展开第一个卡片
    const firstCard = document.querySelector('.collapsible-card');
    if (firstCard) {
        firstCard.classList.add('active');
    }
    
    // 添加滚动动画
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    
    const observer = new IntersectionObserver(function(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, observerOptions);
    
    // 观察所有卡片
    document.querySelectorAll('.guide-card').forEach(card => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px)';
        card.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
        observer.observe(card);
    });
    
    // 添加提示框点击效果
    document.querySelectorAll('.tip-item').forEach(tip => {
        tip.addEventListener('click', function() {
            this.style.transform = 'scale(0.98)';
            setTimeout(() => {
                this.style.transform = '';
            }, 200);
        });
    });
};