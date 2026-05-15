// 当前书籍ID（全局变量）
let currentBookId = null;

// 确保在DOM加载完成前加载dataAccess模块
if (!window.dataAccess) {
    // 动态引入dataAccess.js
    const script = document.createElement('script');
    script.src = '/static/js/dataAccess.js';
    script.onload = async () => {
        console.log('dataAccess模块加载完成');
        // 尝试执行数据迁移（从localStorage到本地文件）
        try {
            await window.dataAccess.migrateLocalStorage();
        } catch (error) {
            console.warn('数据迁移失败，但不影响应用运行:', error);
        }
    };
    document.head.appendChild(script);
}

// 获取书籍信息
async function getBookById(bookId) {
    try {
        if (!bookId) {
            console.error('书籍ID为空');
            return null;
        }
        
        console.log('正在获取书籍信息，ID:', bookId);
        
        // 从API获取书籍数据
        const response = await fetch(`/api/books/${encodeURIComponent(bookId)}`, {
            credentials: 'include'
        });
        
        console.log('API响应状态:', response.status);
        
        if (!response.ok) {
            const errorText = await response.text();
            console.error('API响应失败:', response.status, errorText);
            
            // 尝试解析错误信息
            try {
                const errorData = JSON.parse(errorText);
                throw new Error(errorData.message || `HTTP ${response.status}`);
            } catch (e) {
                throw new Error(`HTTP ${response.status}: ${errorText}`);
            }
        }
        
        const data = await response.json();
        console.log('API返回数据:', data);
        
        if (data.status === 'success' && data.book) {
            const book = data.book;
            
            // 数据字段映射和标准化
            const normalizedBook = {
                id: book.id || '',
                title: book.title || '未知书名',
                author: book.author || '未知作者',
                category: book.category || '',
                price: parseFloat(book.price || 0),
                stock: book.stock !== undefined ? book.stock : (book.status === 'available' ? 1 : 0),
                createTime: book.created_at || book.createTime || book.publish_date || '',
                description: book.description || '',
                imgs: (() => {
                    if (book.cover_url) return [book.cover_url];
                    if (Array.isArray(book.imgs) && book.imgs.length > 0) return book.imgs;
                    if (book.image) return [book.image];
                    return ['https://picsum.photos/id/48/400/300'];
                })(),
                seller: book.owner_name || book.seller || '匿名用户',
                sellerId: book.owner_id || book.sellerId || book.owner_name || 0,
                contact: book.contact || '未提供联系方式',
                status: book.status || 'available'
            };
            
            console.log('书籍信息标准化完成:', normalizedBook);
            return normalizedBook;
        } else {
            console.error('获取书籍信息失败:', data.message || '未知错误');
            return null;
        }
    } catch (error) {
        console.error('获取书籍信息出错:', error);
        console.error('错误详情:', error.message, error.stack);
        return null;
    }
}

// 获取分类名称
function getCategoryName(category) {
    const categoryMap = {
        "textbook": "教材教辅",
        "postgraduate": "考研资料",
        "literature": "文学小说",
        "professional": "专业书籍",
        "other": "其他书籍"
    };
    return categoryMap[category] || "未知分类";
}
// 自动回复规则
const autoReplyRules = {
    "你好": "您好！很高兴为您服务，请问有什么可以帮助您的吗？",
    "价格": "我们的商品价格在商品详情页有明确标注哦，您可以查看一下~ 有活动时会有优惠呢",
    "多少钱": "这本书的价格是页面上显示的价格哦，暂时没有折扣呢",
    "发货": "一般情况下，下单后48小时内会为您安排发货的，请您耐心等待~",
    "售后": "如果您有售后问题，可以先查看一下售后政策，或者告诉我具体情况，我会尽力为您处理",
    "几成新": "这本书有9成新哦，页面没有明显破损和笔记",
    "包邮吗": "抱歉呢，暂时不提供包邮服务，需要您自付运费",
    "默认": "不好意思，暂时没理解您的意思呢~ 您可以换种方式描述一下您的问题吗？"
};

// 页面加载完成后执行
document.addEventListener('DOMContentLoaded', async function() {
    try {
        // 更新用户菜单
        if (typeof updateUserMenu === 'function') {
            updateUserMenu();
        }
        
        // 获取URL中的书籍ID
        const urlParams = new URLSearchParams(window.location.search);
        currentBookId = urlParams.get('id');
        // 同步到 window 对象，供 comments.js 使用
        window.currentBookId = currentBookId;
        
        if (!currentBookId) {
            alert('未找到书籍信息');
            window.location.href = '/booksList';
            return;
        }
        
        // 加载书籍详情
        await loadBookDetails(currentBookId);
        
        // 检查是否已收藏（仅当用户已登录时）
        const user = getCurrentUser();
        if (user) {
            await checkIfCollected(currentBookId);
        }
        
        // 初始化评论功能
        if (typeof initComments === 'function') {
            initComments(currentBookId);
        }
        
        // 绑定收藏按钮事件
        const collectBtn = document.getElementById('collectBtn');
        if (collectBtn) {
            collectBtn.addEventListener('click', async function() {
                await toggleCollection(currentBookId);
            });
        }
        
        // 绑定联系卖家按钮事件
        const contactBtn = document.getElementById('contactSellerBtn');
        if (contactBtn) {
            contactBtn.addEventListener('click', function() {
                openContactModal();
            });
        }
        
        // 绑定购买按钮事件
        const buyBtn = document.getElementById('buyBookBtn');
        if (buyBtn) {
            buyBtn.addEventListener('click', function() {
                handleBuyBook();
            });
            
            // 检查当前用户是否已经购买了这本书
            await checkIfBought();
        }
        
        // 绑定添加到购物车按钮事件
        const addToCartBtn = document.getElementById('addToCartBtn');
        if (addToCartBtn) {
            addToCartBtn.addEventListener('click', function() {
                handleAddToCart();
            });
            
            // 检查是否已在购物车中
            await checkIfInCart();
        }
        
        // 绑定发送消息按钮事件
        const sendMessageBtn = document.getElementById('sendMessageBtn');
        if (sendMessageBtn) {
            sendMessageBtn.addEventListener('click', sendMessage);
        }
        
        const messageInput = document.getElementById('messageInput');
        if (messageInput) {
            messageInput.addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    sendMessage();
                }
            });
        }
    } catch (error) {
        console.error('页面初始化失败:', error);
        alert('页面加载失败，请刷新页面重试');
    }
});

// 加载书籍详情
async function loadBookDetails(bookId) {
    const book = await getBookById(bookId);
    if (!book) {
        alert('未找到书籍信息');
        window.location.href = '/booksList';
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
    
    // 填充书籍信息
    document.getElementById('bookTitle').textContent = escapeHtml(book.title);
    document.getElementById('bookAuthor').textContent = escapeHtml(book.author || '未知作者');
    document.getElementById('bookPrice').textContent = escapeHtml(book.price.toFixed(2));
    document.getElementById('bookDescription').textContent = escapeHtml(book.description || '暂无描述');
    document.getElementById('bookCategory').textContent = escapeHtml(getCategoryName(book.category));
    document.getElementById('bookPublishTime').textContent = escapeHtml(book.createTime);
    document.getElementById('bookSeller').textContent = escapeHtml(book.seller);
    // 使用common.js中的getStatusText函数
    const statusText = typeof getStatusText === 'function' ? getStatusText(book.status) : (book.status === 'available' ? '在售' : '已售出');
    document.getElementById('bookStatus').textContent = statusText;
    
    // 设置书籍图片
    if (book.imgs && book.imgs.length > 0) {
        document.getElementById('bookImage').src = book.imgs[0];
    } else {
        document.getElementById('bookImage').src = 'img/default-book.jpg'; // 默认图片
    }
    
    // 填充卖家信息
    document.getElementById('sellerName').textContent = escapeHtml(book.seller);
    // 新增：显示卖家联系方式
    document.getElementById('sellerContact').textContent = escapeHtml(book.contact || '未提供联系方式');
    
    // 设置模态框中的卖家名称
    document.getElementById('modalSellerName').textContent = escapeHtml(book.seller);
}

// 检查是否已收藏
async function checkIfCollected(bookId) {
    const user = getCurrentUser();
    if (!user) return;
    
    try {
        const response = await fetch(`/api/collections/check/${bookId}`, {
            credentials: 'include'
        });
        
        if (!response.ok) {
            return;
        }
        
        const result = await response.json();
        
        if (result.status === 'success') {
            const collectBtn = document.getElementById('collectBtn');
            if (result.is_collected) {
                collectBtn.innerHTML = '<i class="fa fa-star"></i> 已收藏';
                collectBtn.classList.add('collected');
            } else {
                collectBtn.innerHTML = '<i class="fa fa-star-o"></i> 收藏书籍';
                collectBtn.classList.remove('collected');
            }
        }
    } catch (error) {
        console.error('检查收藏状态失败:', error);
    }
}

// 切换收藏状态
async function toggleCollection(bookId) {
    const user = getCurrentUser();
    if (!user) {
        if (confirm('收藏需要先登录，是否去登录？')) {
            window.location.href = `/login?redirect=/book1?id=${bookId}`;
        }
        return;
    }
    
    try {
        const response = await fetch(`/api/collections/${bookId}`, {
            method: 'POST',
            credentials: 'include'
        });
        
        const result = await response.json();
        
        if (result.status === 'success') {
            const collectBtn = document.getElementById('collectBtn');
            if (result.is_collected) {
                collectBtn.innerHTML = '<i class="fa fa-star"></i> 已收藏';
                collectBtn.classList.add('collected');
            } else {
                collectBtn.innerHTML = '<i class="fa fa-star-o"></i> 收藏书籍';
                collectBtn.classList.remove('collected');
            }
        } else {
            alert('操作失败：' + (result.message || '未知错误'));
        }
    } catch (error) {
        console.error('切换收藏状态失败:', error);
        alert('操作失败，请稍后重试');
    }
}

// 打开联系卖家模态框
async function openContactModal() {
    if (!checkLogin()) {
        if (confirm('联系卖家需要先登录，是否去登录？')) {
            window.location.href = `/login?redirect=/book1?id=${currentBookId}`;
        }
        return;
    }
    
    try {
        const book = await getBookById(currentBookId);
        if (!book) {
            alert('获取书籍信息失败');
            return;
        }
        
        // 显示模态框
        const modalElement = document.getElementById('contactModal');
        if (!modalElement) {
            alert('联系卖家功能暂不可用');
            return;
        }
        
        const contactModal = new bootstrap.Modal(modalElement);
        contactModal.show();
        
        // 绑定事件
        bindChatEvents();
        
        // 加载聊天记录
        await loadChatHistory(book.sellerId, currentBookId);
        
        // 聚焦输入框
        setTimeout(() => {
            const input = document.getElementById('messageInput');
            if (input) input.focus();
        }, 300);
    } catch (error) {
        console.error('打开联系卖家模态框失败:', error);
        alert('打开聊天窗口失败，请稍后重试');
    }
}

// 绑定聊天相关事件
function bindChatEvents() {
    // 发送按钮
    const sendBtn = document.getElementById('sendMessageBtn');
    if (sendBtn && !sendBtn.hasAttribute('data-bound')) {
        sendBtn.setAttribute('data-bound', 'true');
        sendBtn.addEventListener('click', sendMessage);
    }
    
    // 输入框回车发送
    const messageInput = document.getElementById('messageInput');
    if (messageInput && !messageInput.hasAttribute('data-bound')) {
        messageInput.setAttribute('data-bound', 'true');
        messageInput.addEventListener('keydown', function(e) {
            if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
                e.preventDefault();
                sendMessage();
            }
        });
        
        // 输入框变化时更新发送按钮状态
        messageInput.addEventListener('input', function() {
            updateSendButtonState();
        });
    }
    
    // 清空按钮
    const clearBtn = document.getElementById('clearInputBtn');
    if (clearBtn && !clearBtn.hasAttribute('data-bound')) {
        clearBtn.setAttribute('data-bound', 'true');
        clearBtn.addEventListener('click', function() {
            if (messageInput) {
                messageInput.value = '';
                messageInput.focus();
                updateSendButtonState();
            }
        });
    }
    
    // 快速回复按钮
    const quickReplyBtns = document.querySelectorAll('.quick-reply-btn');
    quickReplyBtns.forEach(btn => {
        if (!btn.hasAttribute('data-bound')) {
            btn.setAttribute('data-bound', 'true');
            btn.addEventListener('click', function() {
                const template = this.getAttribute('data-template');
                useQuickReply(template);
            });
        }
    });
}

// 使用快速回复
function useQuickReply(template) {
    const messageInput = document.getElementById('messageInput');
    if (!messageInput) return;
    
    const quickReplies = {
        '问价': '你好，请问这本书多少钱？',
        '成色': '你好，请问这本书的新旧程度怎么样？有几成新？',
        '地点': '你好，在哪里可以看货？',
        '购买': '你好，我想购买这本书，什么时候方便交易？'
    };
    
    const message = quickReplies[template] || quickReplies['问价'];
    messageInput.value = message;
    messageInput.focus();
    updateSendButtonState();
    
    // 可选：自动发送
    // sendMessage();
}

// 更新发送按钮状态
function updateSendButtonState() {
    const messageInput = document.getElementById('messageInput');
    const sendBtn = document.getElementById('sendMessageBtn');
    
    if (!messageInput || !sendBtn) return;
    
    const hasText = messageInput.value.trim().length > 0;
    sendBtn.disabled = !hasText;
}

// 发送消息
async function sendMessage() {
    const input = document.getElementById('messageInput');
    if (!input) return;
    
    const message = input.value.trim();
    if (!message) return;
    
    const user = getCurrentUser();
    if (!user) {
        alert('请先登录');
        return;
    }
    
    const sendBtn = document.getElementById('sendMessageBtn');
    
    try {
        // 禁用发送按钮
        if (sendBtn) {
            sendBtn.disabled = true;
            sendBtn.innerHTML = '<i class="fa fa-spinner fa-spin"></i>';
        }
        
        const book = await getBookById(currentBookId);
        if (!book) {
            alert('获取书籍信息失败');
            return;
        }
        
        // 创建消息对象
        const messageObj = {
            sender: user.id,
            receiver: book.sellerId || book.owner_id,
            bookId: currentBookId,
            content: message,
            time: new Date().toLocaleTimeString('zh-CN', { 
                hour: '2-digit', 
                minute: '2-digit' 
            }),
            timestamp: Date.now()
        };
        
        // 保存消息到localStorage
        try {
            const messages = JSON.parse(localStorage.getItem('chatMessages') || '[]');
            messages.push(messageObj);
            localStorage.setItem('chatMessages', JSON.stringify(messages));
        } catch (e) {
            console.warn('保存消息失败:', e);
        }
        
        // 显示消息
        addMessageToUI(messageObj, true);
        
        // 清空输入框
        input.value = '';
        updateSendButtonState();
        
        // 显示"正在输入"提示
        showTypingIndicator(true);
        
        // 模拟卖家回复延迟（1-3秒）
        const delay = 1000 + Math.random() * 2000;
        setTimeout(() => {
            showTypingIndicator(false);
            sendAutoReply(message, book.sellerId || book.owner_id, user.id);
        }, delay);
        
    } catch (error) {
        console.error('发送消息失败:', error);
        alert('发送消息失败，请稍后重试');
    } finally {
        // 恢复发送按钮
        if (sendBtn) {
            sendBtn.disabled = false;
            sendBtn.innerHTML = '<i class="fa fa-paper-plane"></i>';
        }
    }
}

// 发送自动回复
async function sendAutoReply(userMessage, senderId, receiverId) {
    try {
        // 获取书籍信息以提供更准确的回复
        const book = await getBookById(currentBookId);
        const bookPrice = book ? book.price : null;
        
        // 改进的自动回复逻辑
        let reply = autoReplyRules["默认"];
        const lowerMessage = userMessage.toLowerCase();
        
        // 价格相关
        if (lowerMessage.includes('价格') || lowerMessage.includes('多少钱') || lowerMessage.includes('多少')) {
            if (bookPrice) {
                reply = `这本书的价格是 ¥${parseFloat(bookPrice).toFixed(2)}，价格很实惠哦~`;
            } else {
                reply = autoReplyRules["价格"];
            }
        }
        // 新旧程度
        else if (lowerMessage.includes('新') || lowerMessage.includes('旧') || lowerMessage.includes('成色')) {
            reply = autoReplyRules["几成新"];
        }
        // 看货/交易地点
        else if (lowerMessage.includes('看货') || lowerMessage.includes('地点') || lowerMessage.includes('在哪') || lowerMessage.includes('交易')) {
            reply = '我们可以在校园内约定地点看货，具体位置可以私下沟通，方便的话也可以直接交易~';
        }
        // 购买/交易
        else if (lowerMessage.includes('买') || lowerMessage.includes('要') || lowerMessage.includes('交易')) {
            reply = '好的，这本书还在售，我们可以约定时间地点当面交易，这样你可以先看货再决定是否购买~';
        }
        // 问候
        else if (lowerMessage.includes('你好') || lowerMessage.includes('您好') || lowerMessage.includes('在吗')) {
            reply = '你好！很高兴为你服务，有什么问题随时问我哦~';
        }
        // 发货
        else if (lowerMessage.includes('发货') || lowerMessage.includes('快递')) {
            reply = autoReplyRules["发货"];
        }
        // 其他关键词匹配
        else {
            for (const [keyword, response] of Object.entries(autoReplyRules)) {
                if (lowerMessage.includes(keyword.toLowerCase()) && keyword !== "默认") {
                    reply = response;
                    break;
                }
            }
        }
        
        // 创建回复消息
        const replyObj = {
            sender: senderId,
            receiver: receiverId,
            bookId: currentBookId,
            content: reply,
            time: new Date().toLocaleTimeString('zh-CN', { 
                hour: '2-digit', 
                minute: '2-digit' 
            }),
            timestamp: Date.now()
        };
        
        // 保存消息到localStorage
        try {
            const messages = JSON.parse(localStorage.getItem('chatMessages') || '[]');
            messages.push(replyObj);
            localStorage.setItem('chatMessages', JSON.stringify(messages));
        } catch (e) {
            console.warn('保存回复消息失败:', e);
        }
        
        // 显示回复
        addMessageToUI(replyObj, false);
    } catch (error) {
        console.error('发送自动回复失败:', error);
    }
}

// 加载聊天记录
async function loadChatHistory(sellerId, bookId) {
    try {
        const user = getCurrentUser();
        if (!user) return;
        
        const messages = await getMessages(user.id, sellerId, bookId);
        
        const container = document.getElementById('messageContainer');
        if (!container) return;
        
        // 创建消息容器
        const messageContainer = document.createElement('div');
        messageContainer.className = 'message-container';
        
        // 添加输入提示指示器
        const typingIndicator = document.createElement('div');
        typingIndicator.className = 'typing-indicator';
        typingIndicator.id = 'typingIndicator';
        typingIndicator.style.display = 'none';
        typingIndicator.innerHTML = `
            <div class="message-avatar">卖</div>
            <div class="message-bubble">
                <div class="typing-dots">
                    <span></span>
                    <span></span>
                    <span></span>
                </div>
            </div>
        `;
        
        messageContainer.appendChild(typingIndicator);
        container.innerHTML = '';
        container.appendChild(messageContainer);
        
        // 如果没有历史消息，显示欢迎消息
        if (messages.length === 0) {
            const welcomeMsg = {
                content: '你好！有什么问题可以随时问我哦~',
                time: new Date().toLocaleTimeString('zh-CN', { 
                    hour: '2-digit', 
                    minute: '2-digit' 
                }),
                timestamp: Date.now()
            };
            addMessageToUI(welcomeMsg, false);
        } else {
            messages.forEach(msg => {
                const isSent = msg.sender === user.id;
                addMessageToUI(msg, isSent);
            });
        }
        
        // 滚动到底部
        setTimeout(() => scrollToBottom(), 100);
    } catch (error) {
        console.error('加载聊天记录失败:', error);
    }
}

// 添加消息到界面
function addMessageToUI(message, isSent) {
    const container = document.querySelector('.message-container');
    if (!container) return;
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `message-item ${isSent ? 'message-sent' : 'message-received'}`;
    
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
    
    // 获取用户信息以显示头像
    const user = getCurrentUser();
    const avatarText = isSent 
        ? (user && user.username ? user.username.charAt(0).toUpperCase() : '我')
        : '卖';
    
    // 格式化时间显示
    const timeDisplay = formatMessageTime(message.timestamp || Date.now(), message.time);
    
    messageDiv.innerHTML = `
        <div class="message-avatar">${avatarText}</div>
        <div class="message-bubble">
            <div class="message-content">${escapeHtml(message.content)}</div>
            <div class="message-time">${escapeHtml(timeDisplay)}</div>
        </div>
    `;
    
    // 插入到输入提示上方
    const typingIndicator = document.getElementById('typingIndicator');
    if (typingIndicator && typingIndicator.parentElement) {
        container.insertBefore(messageDiv, typingIndicator);
    } else {
        container.appendChild(messageDiv);
    }
    
    // 平滑滚动到底部
    scrollToBottom();
}

// 格式化消息时间
function formatMessageTime(timestamp, fallbackTime) {
    if (!timestamp) {
        return fallbackTime || new Date().toLocaleTimeString('zh-CN', { 
            hour: '2-digit', 
            minute: '2-digit' 
        });
    }
    
    const now = new Date();
    const msgTime = new Date(timestamp);
    const diff = now - msgTime;
    const diffSeconds = Math.floor(diff / 1000);
    const diffMinutes = Math.floor(diffSeconds / 60);
    const diffHours = Math.floor(diffMinutes / 60);
    const diffDays = Math.floor(diffHours / 24);
    
    // 今天
    if (diffDays === 0) {
        if (diffMinutes < 1) {
            return '刚刚';
        } else if (diffMinutes < 60) {
            return `${diffMinutes}分钟前`;
        } else {
            return msgTime.toLocaleTimeString('zh-CN', { 
                hour: '2-digit', 
                minute: '2-digit' 
            });
        }
    }
    // 昨天
    else if (diffDays === 1) {
        return '昨天 ' + msgTime.toLocaleTimeString('zh-CN', { 
            hour: '2-digit', 
            minute: '2-digit' 
        });
    }
    // 更早
    else {
        return msgTime.toLocaleDateString('zh-CN', { 
            month: '2-digit', 
            day: '2-digit',
            hour: '2-digit', 
            minute: '2-digit' 
        });
    }
}

// 平滑滚动到底部
function scrollToBottom() {
    const container = document.querySelector('.contact-modal .modal-body');
    if (container) {
        container.scrollTo({
            top: container.scrollHeight,
            behavior: 'smooth'
        });
    }
}

// 显示/隐藏"正在输入"提示
function showTypingIndicator(show) {
    const indicator = document.getElementById('typingIndicator');
    if (indicator) {
        indicator.style.display = show ? 'flex' : 'none';
        if (show) {
            scrollToBottom();
        }
    }
}


// 获取消息历史
async function getMessages(userId1, userId2, bookId) {
    try {
        // 从localStorage获取所有消息
        let messages = [];
        try {
            const stored = localStorage.getItem('chatMessages');
            if (stored) {
                messages = JSON.parse(stored);
            }
        } catch (e) {
            console.warn('读取消息历史失败:', e);
            messages = [];
        }
        
        // 确保messages是数组
        if (!Array.isArray(messages)) {
            messages = [];
        }
        
        // 筛选与当前对话相关的消息
        const filteredMessages = messages.filter(msg => 
            String(msg.bookId) === String(bookId) && 
            ((String(msg.sender) === String(userId1) && String(msg.receiver) === String(userId2)) || 
             (String(msg.sender) === String(userId2) && String(msg.receiver) === String(userId1)))
        );
        
        // 按时间戳排序
        return filteredMessages.sort((a, b) => (a.timestamp || 0) - (b.timestamp || 0));
    } catch (error) {
        console.error('获取消息历史失败:', error);
        return [];
    }
}

// 检查登录状态
function checkLogin() {
    const user = getCurrentUser();
    if (!user) {
        alert('请先登录');
        return false;
    }
    return true;
}

// 处理购买书籍
async function handleBuyBook() {
    try {
        console.log('handleBuyBook called, currentBookId:', currentBookId);
        
        // 检查用户是否登录
        const currentUser = getCurrentUser();
        if (!currentUser) {
            if (confirm('购买书籍需要先登录，是否去登录？')) {
                window.location.href = `/login?redirect=/book1?id=${currentBookId}`;
            }
            return;
        }

        // 获取书籍信息
        const bookInfo = await getBookById(currentBookId);
        if (!bookInfo) {
            alert('获取书籍信息失败');
            return;
        }

        // 获取页面中的书籍标题和价格，作为备用
        let bookTitle = bookInfo.title;
        let bookPrice = bookInfo.price;
        
        // 从页面元素中获取可能更新的标题和价格
        const titleElement = document.querySelector('.book-title');
        const priceElement = document.querySelector('.book-price');
        
        if (titleElement) {
            bookTitle = titleElement.textContent.trim();
        }
        
        if (priceElement) {
            // 提取价格数字
            const priceText = priceElement.textContent.trim();
            const match = priceText.match(/¥([\d.]+)/);
            if (match && match[1]) {
                bookPrice = parseFloat(match[1]);
            }
        }

        // 确认购买
        if (!confirm(`确认购买《${bookTitle}》吗？价格：¥${bookPrice.toFixed(2)}`)) {
            return;
        }

        // 检查书籍是否可购买
        if (bookInfo.status !== 'available') {
            alert('该书籍暂不可购买');
            return;
        }

        // 检查是否购买自己的书
        if (String(currentUser.id) === String(bookInfo.sellerId)) {
            alert('不能购买自己发布的书籍');
            return;
        }

        const response = await fetch('/api/orders', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            credentials: 'include',
            body: JSON.stringify({
                book_id: currentBookId,
                quantity: 1
            })
        });

        if (!response.ok) {
            const errorText = await response.text();
            console.error('API响应错误:', response.status, errorText);
            throw new Error(`HTTP ${response.status}: ${errorText}`);
        }

        const result = await response.json();

        if (result.status === 'success') {
            // 更新按钮状态
            const buyBtn = document.getElementById('buyBookBtn');
            if (buyBtn) {
                buyBtn.disabled = true;
                buyBtn.innerHTML = '<i class="fa fa-check"></i> 已购买';
                buyBtn.classList.add('btn-bought');
                buyBtn.style.cursor = 'not-allowed';
            }
            
            alert('购买成功！书籍已添加到"我买到的"交易记录中');
            
            // 触发购买成功事件
            document.dispatchEvent(new CustomEvent('bookPurchased', { 
                detail: { 
                    order: result.order, 
                    book: bookInfo 
                } 
            }));
        } else {
            alert('购买失败：' + (result.message || '未知错误'));
        }
    } catch (error) {
        console.error('购买过程中发生错误:', error);
        alert('购买过程中发生错误：' + error.message);
    }
}


// 检查当前用户是否已经购买了这本书
async function checkIfBought() {
    const currentUser = getCurrentUser();
    if (!currentUser) {
        return; // 用户未登录，无需检查
    }
    
    try {
        const response = await fetch('/api/orders', {
            credentials: 'include'
        });

        if (!response.ok) {
            return;
        }

        const result = await response.json();

        if (result.status === 'success') {
            const orders = result.orders || [];
            
            // 检查是否有当前用户购买当前书籍的订单
            const hasBought = orders.some(order => {
                const bookMatch = String(order.book_id) === String(currentBookId);
                const statusMatch = order.status === 'completed' || order.status === '已完成';
                return bookMatch && statusMatch;
            });
            
            // 如果已购买，更新按钮状态
            const buyBtn = document.getElementById('buyBookBtn');
            if (hasBought && buyBtn) {
                buyBtn.disabled = true;
                buyBtn.innerHTML = '<i class="fa fa-check"></i> 已购买';
                buyBtn.classList.add('btn-bought');
                buyBtn.style.cursor = 'not-allowed';
            }
            
            return hasBought;
        }
    } catch (error) {
        console.error('检查购买状态失败:', error);
        return false;
    }
}

// 处理添加到购物车
async function handleAddToCart() {
    try {
        console.log('handleAddToCart called, currentBookId:', currentBookId);
        
        // 检查用户是否登录
        const user = getCurrentUser();
        if (!user) {
            if (confirm('添加到购物车需要先登录，是否去登录？')) {
                window.location.href = `/login?redirect=/book1?id=${currentBookId}`;
            }
            return;
        }

        // 获取书籍信息
        const bookInfo = await getBookById(currentBookId);
        if (!bookInfo) {
            alert('获取书籍信息失败');
            return;
        }

        // 检查书籍是否可购买
        if (bookInfo.status !== 'available') {
            alert('该书籍暂不可购买');
            return;
        }

        // 检查是否购买自己的书
        if (String(user.id) === String(bookInfo.sellerId)) {
            alert('不能添加自己发布的书籍到购物车');
            return;
        }

        const response = await fetch('/api/cart', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            credentials: 'include',
            body: JSON.stringify({
                book_id: currentBookId,
                quantity: 1
            })
        });

        if (!response.ok) {
            const errorText = await response.text();
            console.error('API响应错误:', response.status, errorText);
            throw new Error(`HTTP ${response.status}: ${errorText}`);
        }

        const result = await response.json();

        if (result.status === 'success') {
            alert('已添加到购物车！');
            
            // 更新按钮状态
            const addToCartBtn = document.getElementById('addToCartBtn');
            if (addToCartBtn) {
                addToCartBtn.innerHTML = '<i class="fa fa-check"></i> 已在购物车';
                addToCartBtn.classList.add('btn-in-cart');
            }
        } else {
            alert('添加到购物车失败：' + (result.message || '未知错误'));
        }
    } catch (error) {
        console.error('添加到购物车失败:', error);
        alert('添加到购物车时发生错误：' + error.message);
    }
}

// 检查是否已在购物车中
async function checkIfInCart() {
    const user = getCurrentUser();
    if (!user) {
        return;
    }

    try {
        const response = await fetch('/api/cart', {
            credentials: 'include'
        });

        if (!response.ok) {
            return;
        }

        const result = await response.json();

        if (result.status === 'success') {
            const cartItems = result.cart || [];
            const isInCart = cartItems.some(item => 
                String(item.book_id) === String(currentBookId)
            );

            if (isInCart) {
                const addToCartBtn = document.getElementById('addToCartBtn');
                if (addToCartBtn) {
                    addToCartBtn.innerHTML = '<i class="fa fa-check"></i> 已在购物车';
                    addToCartBtn.classList.add('btn-in-cart');
                }
            }
        }
    } catch (error) {
        console.error('检查购物车状态失败:', error);
    }
}

// 获取当前用户（兼容common.js）
function getCurrentUser() {
    try {
        // 优先使用common.js中的getCurrentUser函数
        if (typeof window.getCurrentUser === 'function' && window.getCurrentUser !== getCurrentUser) {
            return window.getCurrentUser();
        }
        const userStr = localStorage.getItem('currentUser');
        return userStr ? JSON.parse(userStr) : null;
    } catch (e) {
        console.error('获取用户信息失败:', e);
        return null;
    }
}