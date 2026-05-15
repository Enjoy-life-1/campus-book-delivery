// 存储已预览的图片
const previewImages = [];
// 编辑模式的书籍ID
let editBookId = null;

// 页面加载时初始化
document.addEventListener('DOMContentLoaded', function() {
    // 确保common.js已加载
    if (typeof checkLogin !== 'function') {
        console.error('checkLogin函数未定义，请确保common.js已加载');
        return;
    }
    
    // 检查登录状态
    if (!checkLogin('/publishBook')) {
        return;
    }
    
    // 更新用户菜单
    if (typeof updateUserMenu === 'function') {
        updateUserMenu();
    }
    
    // 初始化图片预览
    setupImagePreview();
    
    // 检查是否是编辑模式
    const urlParams = new URLSearchParams(window.location.search);
    editBookId = urlParams.get('edit');
    if (editBookId) {
        loadBookForEdit(editBookId);
    }
    
    // 预填分类（从URL参数获取）
    const defaultCategory = urlParams.get('category');
    if (defaultCategory && !editBookId) {
        document.getElementById('bookCategory').value = defaultCategory;
    }
    
    // 表单提交事件
    const publishForm = document.getElementById('publishForm');
    if (publishForm) {
        publishForm.addEventListener('submit', handleFormSubmit);
    }
});

// 图片预览功能
function setupImagePreview() {
    // 为每个图片输入框添加change事件
    ['img1', 'img2', 'img3'].forEach((inputId, index) => {
        const input = document.getElementById(inputId);
        if (input) {
            input.addEventListener('change', function(e) {
                const file = e.target.files[0];
                if (file) {
                    // 验证文件类型
                    if (!file.type.startsWith('image/')) {
                        alert('请选择图片文件');
                        e.target.value = '';
                        return;
                    }
                    
                    // 验证文件大小（限制为5MB）
                    if (file.size > 5 * 1024 * 1024) {
                        alert('图片大小不能超过5MB');
                        e.target.value = '';
                        return;
                    }
                    
                    const reader = new FileReader();
                    reader.onload = function(event) {
                        previewImages[index] = {
                            file: file,
                            url: event.target.result
                        };
                        updateImagePreviews();
                    };
                    reader.readAsDataURL(file);
                }
            });
        }
    });
}

// 更新图片预览
function updateImagePreviews() {
    const container = document.getElementById('imagePreviewContainer');
    if (!container) return;
    
    container.innerHTML = '';
    
    previewImages.forEach((img, index) => {
        if (img) {
            const previewDiv = document.createElement('div');
            previewDiv.className = 'image-preview';
            previewDiv.innerHTML = `
                <img src="${img.url}" alt="预览图">
                <span class="remove-image" data-index="${index}">×</span>
            `;
            container.appendChild(previewDiv);
        }
    });
    
    // 添加删除图片事件
    document.querySelectorAll('.remove-image').forEach(btn => {
        btn.addEventListener('click', function() {
            const index = parseInt(this.getAttribute('data-index'));
            // 清空对应input的值
            const input = document.getElementById(`img${index + 1}`);
            if (input) {
                input.value = '';
            }
            // 移除预览图
            previewImages[index] = null;
            updateImagePreviews();
        });
    });
}

// 加载编辑的书籍数据
async function loadBookForEdit(bookId) {
    try {
        const response = await fetch(`/api/books/${bookId}`, {
            credentials: 'include'
        });
        
        if (!response.ok) {
            alert('未找到该书籍信息');
            window.location.href = '/myBooks';
            return;
        }
        
        const result = await response.json();
        if (result.status === 'success' && result.book) {
            const book = result.book;
            
            // 填充表单数据
            document.getElementById('bookTitle').value = book.title || '';
            document.getElementById('bookCategory').value = book.category || '';
            document.getElementById('bookAuthor').value = book.author || '';
            document.getElementById('bookPrice').value = book.price || '';
            document.getElementById('bookDesc').value = book.desc || book.description || '';
            document.getElementById('contactInfo').value = book.contact || '';
            
            // 填充图片预览
            const bookImgs = book.imgs || (book.cover_url ? [book.cover_url] : []);
            if (bookImgs.length > 0) {
                bookImgs.forEach((imgUrl, index) => {
                    if (index < 3) {
                        previewImages[index] = { url: imgUrl };
                        const input = document.getElementById(`img${index + 1}`);
                        if (input) {
                            input.value = '';
                        }
                    }
                });
                updateImagePreviews();
            }
            
            // 修改页面标题
            const titleElement = document.querySelector('.publish-title');
            if (titleElement) {
                titleElement.textContent = '编辑书籍信息';
            }
            const submitBtn = document.querySelector('.btn-publish');
            if (submitBtn) {
                submitBtn.textContent = '保存修改';
            }
        }
    } catch (error) {
        console.error('加载书籍信息失败:', error);
        alert('加载书籍信息失败，请刷新重试');
    }
}

// 表单提交处理
async function handleFormSubmit(e) {
    e.preventDefault();
    
    // 收集表单数据
    const title = document.getElementById('bookTitle').value.trim();
    const category = document.getElementById('bookCategory').value;
    const author = document.getElementById('bookAuthor').value.trim();
    const price = parseFloat(document.getElementById('bookPrice').value);
    const desc = document.getElementById('bookDesc').value.trim();
    const contact = document.getElementById('contactInfo').value.trim();
    
    // 表单验证
    if (!title) {
        alert('请填写书籍标题');
        document.getElementById('bookTitle').focus();
        return;
    }
    
    if (!category) {
        alert('请选择书籍分类');
        document.getElementById('bookCategory').focus();
        return;
    }
    
    if (!price || price <= 0 || isNaN(price)) {
        alert('请填写有效的价格（必须大于0）');
        document.getElementById('bookPrice').focus();
        return;
    }
    
    if (!desc) {
        alert('请填写书籍描述');
        document.getElementById('bookDesc').focus();
        return;
    }
    
    if (!contact) {
        alert('请填写联系方式');
        document.getElementById('contactInfo').focus();
        return;
    }
    
    // 处理图片
    const imgs = [];
    previewImages.forEach(img => {
        if (img && img.url) {
            imgs.push(img.url);
        }
    });
    
    if (imgs.length === 0) {
        alert('请至少上传一张书籍图片');
        return;
    }
    
    // 构建书籍数据
    const bookData = {
        title: title,
        category: category,
        author: author || '未知作者',
        price: price,
        desc: desc,
        contact: contact,
        imgs: imgs,
        stock: 1
    };
    
    try {
        let response;
        let result;
        
        if (editBookId) {
            // 编辑模式：更新书籍
            response = await fetch(`/api/books/${editBookId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                credentials: 'include',
                body: JSON.stringify(bookData)
            });
        } else {
            // 新增模式：创建书籍
            response = await fetch('/api/books', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                credentials: 'include',
                body: JSON.stringify(bookData)
            });
        }
        
        if (!response.ok) {
            if (response.status === 401) {
                alert('登录状态已过期，请重新登录');
                window.location.href = '/login?redirect=/publishBook';
                return;
            }
            
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.message || `HTTP错误: ${response.status}`);
        }
        
        result = await response.json();
        
        if (result.status === 'success') {
            alert(editBookId ? '书籍更新成功！' : '发布成功！');
            
            if (editBookId) {
                // 编辑模式：跳转到我的书籍页面
                window.location.href = '/myBooks';
            } else {
                // 新增模式：重置表单
                document.getElementById('publishForm').reset();
                previewImages.length = 0;
                updateImagePreviews();
                
                // 可选：跳转到书籍列表或我的书籍页面
                const goToMyBooks = confirm('发布成功！是否前往"我的书籍"查看？');
                if (goToMyBooks) {
                    window.location.href = '/myBooks';
                }
            }
        } else {
            alert('操作失败：' + (result.message || '未知错误'));
        }
    } catch (error) {
        console.error('发布/更新书籍失败:', error);
        alert('操作失败：' + (error.message || '网络错误，请稍后重试'));
    }
}
