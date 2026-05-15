// login.js - 登录页面功能实现
// 使用common.js中定义的apiRequest函数
// 使用main.js中定义的UI辅助函数(saveUser, showToast, showError, showSuccess等)

// 初始化为学生角色
let currentRole = 'student';
// 当前选中的用户身份

// 从URL查询参数中获取登录信息并自动填充表单
function fillFormFromUrl() {
    // 获取URL中的查询参数
    const urlParams = new URLSearchParams(window.location.search);
    const username = urlParams.get('username');
    const password = urlParams.get('password');
    const role = urlParams.get('role'); // 获取角色参数
    
    // 如果URL中包含角色参数，则切换到对应角色
    // 注意：这个函数在initLoginPage之后调用，但为了确保UI正确更新，我们再次设置角色
    if (role === 'admin' || role === 'student') {
        currentRole = role;
        // 获取所有可能的角色切换按钮
        const roleStudent = document.getElementById('role-student');
        const roleAdmin = document.getElementById('role-admin');
        const studentBtn = document.getElementById('student-btn');
        const adminBtn = document.getElementById('admin-btn');
        
        // 更新所有可能的UI元素状态 - 使用remove/add而不是toggle，确保状态正确
        if (roleStudent) {
            roleStudent.classList.remove('active');
            if (role === 'student') roleStudent.classList.add('active');
        }
        if (roleAdmin) {
            roleAdmin.classList.remove('active');
            if (role === 'admin') roleAdmin.classList.add('active');
        }
        if (studentBtn) {
            studentBtn.classList.remove('active');
            if (role === 'student') studentBtn.classList.add('active');
        }
        if (adminBtn) {
            adminBtn.classList.remove('active');
            if (role === 'admin') adminBtn.classList.add('active');
        }
        
        // 更新账号输入框的placeholder
        const usernameInput = document.getElementById('username');
        if (usernameInput) {
            usernameInput.placeholder = role === 'student' ? '请输入学号' : '请输入账号';
        }
        
        console.log('从URL参数设置角色为:', role);
    }
    
    // 如果URL中包含用户名和密码参数，则填充到表单中
    if (username && password) {
        const usernameInput = document.getElementById('username');
        const passwordInput = document.getElementById('password');
        
        if (usernameInput && passwordInput) {
            // 移除参数值中可能的前导空格（处理+号问题）
            usernameInput.value = username.trim();
            passwordInput.value = password;
            
            // 自动提交表单
            document.getElementById('loginForm')?.submit();
        }
    }
}

// 统一的角色切换功能
function setupRoleToggle() {
    // 支持两套不同的角色选择UI元素
    const roleStudent = document.getElementById('role-student');
    const roleAdmin = document.getElementById('role-admin');
    const studentBtn = document.getElementById('student-btn');
    const adminBtn = document.getElementById('admin-btn');
    
    // 设置所有可能的角色切换按钮的事件监听器
    function setRole(role) {
        currentRole = role;
        console.log('角色已切换为:', role);
        // 更新所有可能的UI元素状态
        if (roleStudent) roleStudent.classList.toggle('active', role === 'student');
        if (roleAdmin) roleAdmin.classList.toggle('active', role === 'admin');
        if (studentBtn) studentBtn.classList.toggle('active', role === 'student');
        if (adminBtn) adminBtn.classList.toggle('active', role === 'admin');
        
        // 更新账号输入框的placeholder
        const usernameInput = document.getElementById('username');
        if (usernameInput) {
            usernameInput.placeholder = role === 'student' ? '请输入学号' : '请输入账号';
        }
    }
    
    if (roleStudent) roleStudent.addEventListener('click', () => setRole('student'));
    if (roleAdmin) roleAdmin.addEventListener('click', () => setRole('admin'));
    if (studentBtn) studentBtn.addEventListener('click', () => setRole('student'));
    if (adminBtn) adminBtn.addEventListener('click', () => setRole('admin'));
    
    // 初始化UI状态
    setRole(currentRole);
}

// 添加MD5哈希函数用于密码哈希计算
// 纯JavaScript实现的MD5算法，确保与后端Python的hashlib.md5计算结果一致
function md5(str) {
    return new Promise((resolve) => {
        // 完整的MD5哈希算法实现
        // 参考：https://github.com/blueimp/JavaScript-MD5
        const md5hash = function(str) {
            function rotateLeft(lValue, iShiftBits) {
                return (lValue << iShiftBits) | (lValue >>> (32 - iShiftBits));
            }
            function addUnsigned(lX, lY) {
                var lX4, lY4, lX8, lY8, lResult;
                lX8 = (lX & 0x80000000);
                lY8 = (lY & 0x80000000);
                lX4 = (lX & 0x40000000);
                lY4 = (lY & 0x40000000);
                lResult = (lX & 0x3FFFFFFF) + (lY & 0x3FFFFFFF);
                if (lX4 & lY4) {
                    return (lResult ^ 0x80000000 ^ lX8 ^ lY8);
                }
                if (lX4 | lY4) {
                    if (lResult & 0x40000000) {
                        return (lResult ^ 0xC0000000 ^ lX8 ^ lY8);
                    } else {
                        return (lResult ^ 0x40000000 ^ lX8 ^ lY8);
                    }
                } else {
                    return (lResult ^ lX8 ^ lY8);
                }
            }
            function F(x, y, z) { return (x & y) | ((~x) & z); }
            function G(x, y, z) { return (x & z) | (y & (~z)); }
            function H(x, y, z) { return (x ^ y ^ z); }
            function I(x, y, z) { return (y ^ (x | (~z))); }
            function FF(a, b, c, d, x, s, ac) {
                a = addUnsigned(a, addUnsigned(addUnsigned(F(b, c, d), x), ac));
                return addUnsigned(rotateLeft(a, s), b);
            }
            function GG(a, b, c, d, x, s, ac) {
                a = addUnsigned(a, addUnsigned(addUnsigned(G(b, c, d), x), ac));
                return addUnsigned(rotateLeft(a, s), b);
            }
            function HH(a, b, c, d, x, s, ac) {
                a = addUnsigned(a, addUnsigned(addUnsigned(H(b, c, d), x), ac));
                return addUnsigned(rotateLeft(a, s), b);
            }
            function II(a, b, c, d, x, s, ac) {
                a = addUnsigned(a, addUnsigned(addUnsigned(I(b, c, d), x), ac));
                return addUnsigned(rotateLeft(a, s), b);
            }
            function convertToWordArray(str) {
                var lWordCount;
                var lMessageLength = str.length;
                var lNumberOfWords_temp1=lMessageLength + 8;
                var lNumberOfWords_temp2=(lNumberOfWords_temp1-(lNumberOfWords_temp1%64))/64;
                var lNumberOfWords = (lNumberOfWords_temp2+1)*16;
                var lWordArray=Array(lNumberOfWords-1);
                var lBytePosition = 0;
                var lByteCount = 0;
                while ( lByteCount < lMessageLength ) {
                    lWordCount = (lByteCount-(lByteCount%4))/4;
                    lBytePosition = (lByteCount%4)*8;
                    lWordArray[lWordCount] = (lWordArray[lWordCount] | (str.charCodeAt(lByteCount)<<lBytePosition));
                    lByteCount++;
                }
                lWordCount = (lByteCount-(lByteCount%4))/4;
                lBytePosition = (lByteCount%4)*8;
                lWordArray[lWordCount] = lWordArray[lWordCount] | (0x80<<lBytePosition);
                lWordArray[lNumberOfWords-2] = lMessageLength<<3;
                lWordArray[lNumberOfWords-1] = lMessageLength>>>29;
                return lWordArray;
            }
            function wordToHex(lValue) {
                var WordToHexValue="", WordToHexValue_temp="", lByte, lCount;
                for (lCount = 0;lCount<=3;lCount++) {
                    lByte = (lValue>>>(lCount*8)) & 255;
                    WordToHexValue_temp = "0"+lByte.toString(16);
                    WordToHexValue = WordToHexValue + WordToHexValue_temp.substr(WordToHexValue_temp.length-2,2);
                }
                return WordToHexValue;
            }
            function uTF8Encode(string) {
                string = string.replace(/\\r\\n/g, "\n");
                var utftext = "";
                for (var n = 0; n < string.length; n++) {
                    var c = string.charCodeAt(n);
                    if (c < 128) {
                        utftext += String.fromCharCode(c);
                    } else if ((c > 127) && (c < 2048)) {
                        utftext += String.fromCharCode((c >> 6) | 192);
                        utftext += String.fromCharCode((c & 63) | 128);
                    } else {
                        utftext += String.fromCharCode((c >> 12) | 224);
                        utftext += String.fromCharCode(((c >> 6) & 63) | 128);
                        utftext += String.fromCharCode((c & 63) | 128);
                    }
                }
                return utftext;
            }
            var x=Array();
            var k, AA, BB, CC, DD, a, b, c, d;
            var S11=7, S12=12, S13=17, S14=22;
            var S21=5, S22=9, S23=14, S24=20;
            var S31=4, S32=11, S33=16, S34=23;
            var S41=6, S42=10, S43=15, S44=21;
            str = uTF8Encode(str);
            x = convertToWordArray(str);
            a = 0x67452301;
            b = 0xEFCDAB89;
            c = 0x98BADCFE;
            d = 0x10325476;
            for (k=0;k<x.length;k+=16) {
                AA=a; BB=b; CC=c; DD=d;
                a=FF(a,b,c,d,x[k+0],S11,0xD76AA478);
                b=FF(d,a,b,c,x[k+1],S12,0xE8C7B756);
                c=FF(c,d,a,b,x[k+2],S13,0x242070DB);
                d=FF(b,c,d,a,x[k+3],S14,0xC1BDCEEE);
                a=FF(a,b,c,d,x[k+4],S11,0xF57C0FAF);
                b=FF(d,a,b,c,x[k+5],S12,0x4787C62A);
                c=FF(c,d,a,b,x[k+6],S13,0xA8304613);
                d=FF(b,c,d,a,x[k+7],S14,0xFD469501);
                a=FF(a,b,c,d,x[k+8],S11,0x698098D8);
                b=FF(d,a,b,c,x[k+9],S12,0x8B44F7AF);
                c=FF(c,d,a,b,x[k+10],S13,0xFFFF5BB1);
                d=FF(b,c,d,a,x[k+11],S14,0x895CD7BE);
                a=FF(a,b,c,d,x[k+12],S11,0x6B901122);
                b=FF(d,a,b,c,x[k+13],S12,0xFD987193);
                c=FF(c,d,a,b,x[k+14],S13,0xA679438E);
                d=FF(b,c,d,a,x[k+15],S14,0x49B40821);
                a=GG(a,b,c,d,x[k+1],S21,0xF61E2562);
                b=GG(d,a,b,c,x[k+6],S22,0xC040B340);
                c=GG(c,d,a,b,x[k+11],S23,0x265E5A51);
                d=GG(b,c,d,a,x[k+0],S24,0xE9B6C7AA);
                a=GG(a,b,c,d,x[k+5],S21,0xD62F105D);
                b=GG(d,a,b,c,x[k+10],S22,0x2441453);
                c=GG(c,d,a,b,x[k+15],S23,0xD8A1E681);
                d=GG(b,c,d,a,x[k+4],S24,0xE7D3FBC8);
                a=GG(a,b,c,d,x[k+9],S21,0x21E1CDE6);
                b=GG(d,a,b,c,x[k+14],S22,0xC33707D6);
                c=GG(c,d,a,b,x[k+3],S23,0xF4D50D87);
                d=GG(b,c,d,a,x[k+8],S24,0x455A14ED);
                a=GG(a,b,c,d,x[k+13],S21,0xA9E3E905);
                b=GG(d,a,b,c,x[k+2],S22,0xFCEFA3F8);
                c=GG(c,d,a,b,x[k+7],S23,0x676F02D9);
                d=GG(b,c,d,a,x[k+12],S24,0x8D2A4C8A);
                a=HH(a,b,c,d,x[k+5],S31,0xFFFA3942);
                b=HH(d,a,b,c,x[k+8],S32,0x8771F681);
                c=HH(c,d,a,b,x[k+11],S33,0x6D9D6122);
                d=HH(b,c,d,a,x[k+14],S34,0xFDE5380C);
                a=HH(a,b,c,d,x[k+1],S31,0xA4BEEA44);
                b=HH(d,a,b,c,x[k+4],S32,0x4BDECFA9);
                c=HH(c,d,a,b,x[k+7],S33,0xF6BB4B60);
                d=HH(b,c,d,a,x[k+10],S34,0xBEBFBC70);
                a=HH(a,b,c,d,x[k+13],S31,0x289B7EC6);
                b=HH(d,a,b,c,x[k+0],S32,0xEAA127FA);
                c=HH(c,d,a,b,x[k+3],S33,0xD4EF3085);
                d=HH(b,c,d,a,x[k+6],S34,0x4881D05);
                a=HH(a,b,c,d,x[k+9],S31,0xD9D4D039);
                b=HH(d,a,b,c,x[k+12],S32,0xE6DB99E5);
                c=HH(c,d,a,b,x[k+15],S33,0x1FA27CF8);
                d=HH(b,c,d,a,x[k+2],S34,0xC4AC5665);
                a=II(a,b,c,d,x[k+0],S41,0xF4292244);
                b=II(d,a,b,c,x[k+7],S42,0x432AFF97);
                c=II(c,d,a,b,x[k+14],S43,0xAB9423A7);
                d=II(b,c,d,a,x[k+5],S44,0xFC93A039);
                a=II(a,b,c,d,x[k+12],S41,0x655B59C3);
                b=II(d,a,b,c,x[k+3],S42,0x8F0CCC92);
                c=II(c,d,a,b,x[k+10],S43,0xFFEFF47D);
                d=II(b,c,d,a,x[k+1],S44,0x85845DD1);
                a=II(a,b,c,d,x[k+8],S41,0x6FA87E4F);
                b=II(d,a,b,c,x[k+15],S42,0xFE2CE6E0);
                c=II(c,d,a,b,x[k+6],S43,0xA3014314);
                d=II(b,c,d,a,x[k+13],S44,0x4E0811A1);
                a=II(a,b,c,d,x[k+4],S41,0xF7537E82);
                b=II(d,a,b,c,x[k+11],S42,0xBD3AF235);
                c=II(c,d,a,b,x[k+2],S43,0x2AD7D2BB);
                d=II(b,c,d,a,x[k+9],S44,0xEB86D391);
                a=addUnsigned(a,AA);
                b=addUnsigned(b,BB);
                c=addUnsigned(c,CC);
                d=addUnsigned(d,DD);
            }
            var temp = wordToHex(a)+wordToHex(b)+wordToHex(c)+wordToHex(d);
            return temp.toLowerCase();
        };
        
        // 计算MD5哈希值
        const hashValue = md5hash(str);
        resolve(hashValue);
    });
}

// 登录表单提交处理
async function handleLogin(event) {
    event.preventDefault();
    
    // 验证表单
    const isValid = validateForm('loginForm', {
        username: {
            required: true,
            message: '请输入用户名'
        },
        password: {
            required: true,
            message: '请输入密码',
            minLength: 6,
            minLengthMessage: '密码长度不能少于6位'
        }
    });
    
    if (!isValid) {
        return;
    }
    
    // 获取表单数据 - 确保密码也去除前后空格
    const username = document.getElementById('username').value.trim();
    const password = document.getElementById('password').value.trim();
    
    // 显示加载状态
    const submitButton = document.getElementById('login-submit');
    console.log('登录表单数据:', { username, password, currentRole });
    console.log('登录按钮:', submitButton);
    const originalButtonText = submitButton.innerHTML;
    submitButton.disabled = true;
    submitButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> 登录中...';
    // 发送登录请求
    try {
        // 发送原始密码，后端会进行哈希处理
    console.log('发送原始密码，后端将进行哈希处理');
    
    // 调用登录API，包含用户角色信息
    // 修正API请求路径，common.js会自动添加/api前缀
    const response = await apiRequest('login', {
        method: 'POST',
        body: JSON.stringify({
            username: username,
            password: password,
            role: currentRole
        })
    });
        
        if (response.status === 'success' && response.user) {
            // 保存用户信息
            saveUser(response.user);
            
            // 显示成功提示
            showToast('登录成功', 'success');
            
            // 根据用户角色设置不同的跳转目标
            let targetUrl;
            if (currentRole === 'admin') {
                // 管理员跳转到admin路由
                targetUrl = '/admin';
            } else {
                // 学生跳转到首页
                targetUrl = '/';
            }
            
            // 延迟跳转，让用户看到成功提示
            setTimeout(() => {
                window.location.href = targetUrl;
            }, 1500);
        } else {
            throw new Error(response.message || '登录失败，请检查用户名和密码');
        }
    } catch (error) {
        showError('loginError', error.message);
    } finally {
        // 恢复按钮状态
        submitButton.disabled = false;
        submitButton.innerHTML = originalButtonText;
    }
}

// 注册表单提交处理
async function handleRegister(event) {
    event.preventDefault();
    
    // 验证表单
    const isValid = validateForm('register-form', {
        username: {
            required: true,
            message: '请输入用户名',
            minLength: 3,
            minLengthMessage: '用户名长度不能少于3位'
        },
        password: {
            required: true,
            message: '请输入密码',
            minLength: 6,
            minLengthMessage: '密码长度不能少于6位'
        },
        confirmPassword: {
            required: true,
            message: '请确认密码',
            pattern: function(value) {
                const password = document.getElementById('register-password').value;
                return value === password;
            },
            patternMessage: '两次输入的密码不一致'
        },
        email: {
            required: true,
            message: '请输入邮箱',
            pattern: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
            patternMessage: '请输入有效的邮箱地址'
        }
    });
    
    if (!isValid) {
        return;
    }
    
    // 获取表单数据
    const username = document.getElementById('register-username').value;
    const password = document.getElementById('register-password').value;
    const email = document.getElementById('register-email').value;
    
    // 显示加载状态
    const submitButton = document.getElementById('register-submit');
    const originalButtonText = submitButton.innerHTML;
    submitButton.disabled = true;
    submitButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> 注册中...';
    
    try {
        // 调用注册API
        const response = await apiRequest('/register', {
            method: 'POST',
            body: JSON.stringify({ username, password, email })
        });
        
        if (response.status === 'success') {
            // 显示成功提示
            showSuccess('register-message', '注册成功，请登录');
            
            // 切换到登录表单
            switchToLogin();
            
            // 清空注册表单
            document.getElementById('register-form').reset();
        } else {
            throw new Error(response.message || '注册失败');
        }
    } catch (error) {
        showError('register-message', error.message);
    } finally {
        // 恢复按钮状态
        submitButton.disabled = false;
        submitButton.innerHTML = originalButtonText;
    }
}

// 切换到登录表单
function switchToLogin() {
    document.getElementById('login-form-container').style.display = 'block';
    document.getElementById('register-form-container').style.display = 'none';
    document.getElementById('login-tab').classList.add('active');
    document.getElementById('register-tab').classList.remove('active');
    
    // 聚焦到用户名输入框
    document.getElementById('username').focus();
}

// 切换到注册表单
function switchToRegister() {
    document.getElementById('login-form-container').style.display = 'none';
    document.getElementById('register-form-container').style.display = 'block';
    document.getElementById('register-tab').classList.add('active');
    document.getElementById('login-tab').classList.remove('active');
    
    // 聚焦到注册用户名输入框
    document.getElementById('register-username').focus();
}

// 当前选中的用户身份

// 保持兼容性，保留switchRole函数但委托给setupRoleToggle中的setRole
function switchRole(role) {
    currentRole = role;
    // 重新设置UI状态
    setupRoleToggle();
}

// ========== 新增：手机号验证码登录功能 ==========
function initSmsLogin() {
    const smsLoginPrompt = document.querySelector('.sms-login-prompt');
    const passwordLoginPrompt = document.querySelector('.password-login-prompt');
    const loginForm = document.getElementById('loginForm');
    const smsLoginForm = document.getElementById('smsLoginForm');
    const getSmsCodeBtn = document.getElementById('getSmsCode');
    const smsLoginSubmit = document.getElementById('smsLoginSubmit');

    // 切换到验证码登录
    if (smsLoginPrompt && loginForm && smsLoginForm) {
        smsLoginPrompt.addEventListener('click', () => {
            loginForm.style.display = 'none';
            smsLoginForm.style.display = 'block';
        });
    }

    // 切换回密码登录
    if (passwordLoginPrompt && loginForm && smsLoginForm) {
        passwordLoginPrompt.addEventListener('click', () => {
            smsLoginForm.style.display = 'none';
            loginForm.style.display = 'block';
        });
    }

    // 获取验证码（带倒计时）
    if (getSmsCodeBtn) {
        getSmsCodeBtn.addEventListener('click', () => {
            const phone = document.getElementById('smsPhone').value.trim();
            // 手机号格式验证
            if (!/^1[3-9]\d{9}$/.test(phone)) {
                showError('smsLoginError', '请输入正确的手机号');
                return;
            }

            // 倒计时逻辑
            let countdown = 60;
            getSmsCodeBtn.disabled = true;
            getSmsCodeBtn.textContent = `重新发送(${countdown})`;
            
            // 模拟发送验证码（实际项目替换为真实接口）
            console.log(`向手机号 ${phone} 发送验证码`);
            
            const timer = setInterval(() => {
                countdown--;
                getSmsCodeBtn.textContent = `重新发送(${countdown})`;
                if (countdown <= 0) {
                    clearInterval(timer);
                    getSmsCodeBtn.disabled = false;
                    getSmsCodeBtn.textContent = '获取验证码';
                }
            }, 1000);
        });
    }

    // 验证码登录提交
    if (smsLoginSubmit) {
        smsLoginSubmit.addEventListener('click', async () => {
            const phone = document.getElementById('smsPhone').value.trim();
            const code = document.getElementById('smsCode').value.trim();

            // 表单验证
            if (!/^1[3-9]\d{9}$/.test(phone)) {
                showError('smsLoginError', '请输入正确的手机号');
                return;
            }
            if (!code || code.length !== 6) {
                showError('smsLoginError', '请输入6位验证码');
                return;
            }

            // 提交逻辑
            smsLoginSubmit.disabled = true;
            smsLoginSubmit.innerHTML = '<span class="spinner-border spinner-border-sm"></span> 登录中...';

            try {
                // 调用你的API函数（复用你原有逻辑）
                const response = await apiRequest('login/sms', {
                    method: 'POST',
                    body: JSON.stringify({ phone, code, role: currentRole })
                });

                if (response.status === 'success' && response.user) {
                    saveUser(response.user); // 复用你原有保存用户的逻辑
                    showError('smsLoginError', '');
                    // 跳转逻辑（和密码登录一致）
                    setTimeout(() => {
                        window.location.href = currentRole === 'admin' ? '/admin' : '/';
                    }, 1500);
                } else {
                    throw new Error(response.message || '验证码错误或已过期');
                }
            } catch (error) {
                showError('smsLoginError', error.message);
            } finally {
                smsLoginSubmit.disabled = false;
                smsLoginSubmit.innerHTML = '<i class="fa fa-mobile"></i> 验证码登录';
            }
        });
    }
}
// ========== 新增：忘记密码功能 ==========
function initForgotPassword() {
    const forgotPasswordLink = document.getElementById('forgotPasswordLink');
    const forgotPasswordModalElement = document.getElementById('forgotPasswordModal');
    const forgotPasswordModal = new bootstrap.Modal(forgotPasswordModalElement);
    const getResetCodeBtn = document.getElementById('getResetCode');
    const resetPasswordSubmit = document.getElementById('resetPasswordSubmit');
    const cancelResetBtn = document.getElementById('cancelResetBtn');
    const closeForgotModalBtn = document.getElementById('closeForgotModalBtn');
    

    // 打开忘记密码模态框
    if (forgotPasswordLink && forgotPasswordModalElement) {
        forgotPasswordLink.addEventListener('click', (e) => {
            e.preventDefault();
            forgotPasswordModal.show();
        });
    }
    
    // Bootstrap会自动处理backdrop和关闭按钮，但我们也可以添加自定义逻辑
    // 关闭模态框时清理表单和backdrop
    if (forgotPasswordModalElement) {
        forgotPasswordModalElement.addEventListener('hidden.bs.modal', () => {
            // 关闭后清空表单
            const resetPhone = document.getElementById('resetPhone');
            const resetCode = document.getElementById('resetCode');
            const newPassword = document.getElementById('newPassword');
            if (resetPhone) resetPhone.value = '';
            if (resetCode) resetCode.value = '';
            if (newPassword) newPassword.value = '';
            
            // 清理可能残留的backdrop，防止黑屏
            const backdrops = document.querySelectorAll('.modal-backdrop');
            backdrops.forEach(backdrop => {
                backdrop.remove();
            });
            
            // 移除body上的modal-open类和样式，恢复页面滚动
            document.body.classList.remove('modal-open');
            document.body.style.overflow = '';
            document.body.style.paddingRight = '';
        });
    }

    // 获取重置密码验证码
    if (getResetCodeBtn) {
        getResetCodeBtn.addEventListener('click', () => {
            const phone = document.getElementById('resetPhone').value.trim();
            if (!/^1[3-9]\d{9}$/.test(phone)) {
                alert('请输入正确的手机号'); // 若你有showToast函数，可替换为showToast('xxx', 'error')
                return;
            }

            // 倒计时逻辑
            let countdown = 60;
            getResetCodeBtn.disabled = true;
            getResetCodeBtn.textContent = `重新发送(${countdown})`;
            
            // 模拟发送验证码（实际替换为你的API）
            console.log(`向手机号 ${phone} 发送重置密码验证码`);
            
            const timer = setInterval(() => {
                countdown--;
                getResetCodeBtn.textContent = `重新发送(${countdown})`;
                if (countdown <= 0) {
                    clearInterval(timer);
                    getResetCodeBtn.disabled = false;
                    getResetCodeBtn.textContent = '获取验证码';
                }
            }, 1000);
        });
    }

    // 提交密码重置
    if (resetPasswordSubmit) {
        resetPasswordSubmit.addEventListener('click', async () => {
            const phone = document.getElementById('resetPhone').value.trim();
            const code = document.getElementById('resetCode').value.trim();
            const newPassword = document.getElementById('newPassword').value.trim();

            // 表单验证
            if (!/^1[3-9]\d{9}$/.test(phone)) {
                alert('请输入正确的手机号');
                return;
            }
            if (!code || code.length !== 6) {
                alert('请输入6位验证码');
                return;
            }
            if (newPassword.length < 6) {
                alert('密码长度不能少于6位');
                return;
            }

            // 提交逻辑
            resetPasswordSubmit.disabled = true;
            resetPasswordSubmit.textContent = '重置中...';

            try {
                // 调用你的API函数
                const response = await apiRequest('password/reset', {
                    method: 'POST',
                    body: JSON.stringify({ phone, code, newPassword })
                });

                if (response.status === 'success') {
                    alert('密码重置成功，请登录');
                    forgotPasswordModal.hide();
                } else {
                    throw new Error(response.message || '重置失败，请重试');
                }
            } catch (error) {
                alert(error.message);
            } finally {
                resetPasswordSubmit.disabled = false;
                resetPasswordSubmit.textContent = '重置密码';
            }
        });
    }
    
}
function closeForgotModal() {
  // 1. 关闭模态框（用Bootstrap的方法）
  const modal = bootstrap.Modal.getInstance(document.getElementById('forgotPasswordModal'));
  if (modal) modal.hide();

  // 2. 清理可能残留的backdrop，防止黑屏
  setTimeout(() => {
    const backdrops = document.querySelectorAll('.modal-backdrop');
    backdrops.forEach(backdrop => {
      backdrop.remove();
    });
    
    // 移除body上的modal-open类和样式，恢复页面滚动
    document.body.classList.remove('modal-open');
    document.body.style.overflow = '';
    document.body.style.paddingRight = '';
  }, 100);

  // 3. 强制显示登录表单（回到登录页核心）
  document.getElementById('loginForm').style.display = 'block'; // 显示密码登录表单
  document.getElementById('smsLoginForm').style.display = 'none'; // 隐藏验证码表单

  // 4. 清空忘记密码的输入内容（可选，优化体验）
  document.getElementById('resetPhone').value = '';
  document.getElementById('resetCode').value = '';
  document.getElementById('newPassword').value = '';

  // 5. 聚焦到登录表单的用户名输入框（视觉上回归登录页）
  document.getElementById('username').focus();
}

// 初始化登录页面
function initLoginPage() {
    // 先检查URL参数中的角色，如果有则设置currentRole
    const urlParams = new URLSearchParams(window.location.search);
    const role = urlParams.get('role');
    if (role === 'admin' || role === 'student') {
        currentRole = role;
    }
    
    // 绑定表单提交事件 - 确保登录表单有正确的事件监听器
    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
        loginForm.addEventListener('submit', handleLogin);
    }
    
    // 初始化角色切换功能（此时currentRole已经根据URL参数设置好了）
    setupRoleToggle();
    
    // 不再重复绑定身份选择按钮事件，因为setupRoleToggle已经处理
    
    const registerForm = document.getElementById('register-form');
    if (registerForm) {
        registerForm.addEventListener('submit', handleRegister);
    }
    
    // 绑定标签切换事件
    const loginTab = document.getElementById('login-tab');
    if (loginTab) {
        loginTab.addEventListener('click', switchToLogin);
    }
    
    const registerTab = document.getElementById('register-tab');
    if (registerTab) {
        registerTab.addEventListener('click', switchToRegister);
    }
    
    // 身份选择按钮事件已在setupRoleToggle中处理
    
    // 自动聚焦到用户名输入框
    document.getElementById('username')?.focus();
    initSmsLogin(); // 初始化验证码登录
    initForgotPassword(); // 初始化忘记密码
}

/**
 * 页面加载完成后初始化
 */
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM加载完成，开始初始化登录页面');
    console.log('当前URL路径:', window.location.pathname);
    
    // 修复URL路径判断逻辑 - 包含login.html也认为是登录页面
    if (window.location.pathname === '/login' || window.location.pathname.includes('login.html')) {
        console.log('执行登录页面初始化');
        // 初始化登录页面
        initLoginPage();
        
        // 从URL查询参数中自动填充表单
        fillFormFromUrl();
    }
});

// 添加全局错误处理
errorHandler = function(message, source, lineno, colno, error) {
    // 忽略浏览器扩展相关的错误
    if (message && message.includes('Unchecked runtime.lastError') && 
        message.includes('can not use with devtools')) {
        console.warn('忽略浏览器扩展错误:', message);
        return true; // 阻止默认错误处理
    }
    
    // 记录其他错误
    console.error('JavaScript错误:', message, '行号:', lineno, '列号:', colno);
    console.error('错误详情:', error);
    return true; // 阻止默认错误处理
};

// 检查是否已经设置了错误处理器
if (window.onerror !== errorHandler) {
    window.onerror = errorHandler;
}

// 添加扩展错误捕获
if (window.chrome && window.chrome.runtime) {
    // 保存原始的sendMessage函数
    const originalSendMessage = chrome.runtime.sendMessage;
    
    // 重写sendMessage函数以捕获错误
    chrome.runtime.sendMessage = function(message, callback) {
        try {
            // 包装回调以捕获可能的错误
            const wrappedCallback = function(response) {
                try {
                    if (callback) callback(response);
                } catch (e) {
                    if (!e.message || !e.message.includes('can not use with devtools')) {
                        console.error('Chrome扩展消息回调错误:', e);
                    }
                }
            };
            
            // 调用原始函数
            originalSendMessage.apply(this, [message, wrappedCallback]);
        } catch (e) {
            if (!e.message || !e.message.includes('can not use with devtools')) {
                console.error('Chrome扩展消息发送错误:', e);
            }
        }
    };
}

// 导出公共函数，便于其他模块调用
// 移除export语句，确保浏览器兼容性