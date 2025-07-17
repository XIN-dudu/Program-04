<!-- 登录 -->
<!-- src/views/Login.vue -->
<template>
  <div class="login-bg">
    <!-- 新增：入侵警告弹窗 -->
    <div v-if="showAlert" class="big-alert-overlay">
      <div class="big-alert-box">
        <h1>警告！检测到非法入侵</h1>
        <button @click="closeAlert">关闭</button>
      </div>
    </div>
    <div class="auth-container">
      <div class="auth-box">
        <!-- 登录方式切换 -->
        <div style="text-align:center;margin-bottom:20px;">
          <button @click="showLogin=true" :class="{active:showLogin}" style="margin-right:10px;">账号密码登录</button>
          <button @click="showLogin=false" :class="{active:!showLogin}">邮箱验证码登录</button>
        </div>
        <!-- 账号密码登录表单 -->
        <div v-if="showLogin" class="auth-form login-form">
          <h2 class="form-title">用户登录</h2>
          <form @submit.prevent="handleLogin">
            <div class="form-group">
              <label>用户名：</label>
              <input v-model="loginForm.name" type="text" required placeholder="请输入用户名">
            </div>
            <div class="form-group">
              <label>密码：</label>
              <input v-model="loginForm.password" type="password" required placeholder="请输入密码">
            </div>
            <!-- 点选验证码区域 -->
            <div class="form-group" v-if="captchaImg">
              <label>请依次点击下列文字：</label>
              <span style="color:#d9534f;font-weight:bold;">{{ captchaTargets.join('、') }}</span>
              <div style="margin:10px 0;position:relative;width:320px;height:100px;border:1px solid #ccc;">
                <img :src="'data:image/png;base64,'+captchaImg" @click="handleCaptchaClick" style="width:320px;height:100px;cursor:pointer;"/>
                <span v-for="(pt, idx) in captchaClicks" :key="idx" :style="{position:'absolute',left:pt.x-10+'px',top:pt.y-10+'px',width:'20px',height:'20px',background:'#00a1d6',color:'#fff',borderRadius:'50%',textAlign:'center',lineHeight:'20px',fontSize:'14px',pointerEvents:'none'}">{{ idx+1 }}</span>
              </div>
              <button type="button" @click="refreshCaptcha" style="margin-top:5px;">刷新验证码</button>
            </div>
            <button type="submit" class="submit-btn">
              <span>登录</span>
            </button>
          </form>
          <router-link to="/register" class="switch-link">
            没有账号？立即注册
          </router-link>
        </div>
        <!-- 邮箱验证码登录表单 -->
        <div v-else class="auth-form email-login-form">
          <h2 class="form-title">邮箱登录</h2>
          <form @submit.prevent="handleEmailLogin">
            <div class="form-group">
              <label>邮箱：</label>
              <input v-model="emailForm.email" type="email" required placeholder="请输入注册邮箱">
            </div>
            <!-- 验证码区域：label、输入框、按钮同一行 -->
            <div class="form-group form-group-code">
              <label class="code-label">验证码：</label>
              <input v-model="emailForm.code" type="text" required placeholder="请输入验证码" class="code-input">
              <button type="button" :disabled="sendCodeDisabled" @click="sendEmailCode" class="code-btn">{{ sendCodeText }}</button>
            </div>
            <!-- 点选验证码区域（与账号密码登录共用） -->
            <div class="form-group" v-if="captchaImg">
              <label>请依次点击下列文字：</label>
              <span style="color:#d9534f;font-weight:bold;">{{ captchaTargets.join('、') }}</span>
              <div style="margin:10px 0;position:relative;width:320px;height:100px;border:1.5px solid #b6e6fa;border-radius:10px;background:#f8fafc;box-shadow:0 2px 8px rgba(30,40,90,0.04);">
                <img :src="'data:image/png;base64,'+captchaImg" @click="handleCaptchaClick" style="width:320px;height:100px;cursor:pointer;"/>
                <span v-for="(pt, idx) in captchaClicks" :key="'email-'+idx" :style="{position:'absolute',left:pt.x-10+'px',top:pt.y-10+'px',width:'20px',height:'20px',background:'#00a1d6',color:'#fff',borderRadius:'50%',textAlign:'center',lineHeight:'20px',fontSize:'14px',pointerEvents:'none'}">{{ idx+1 }}</span>
              </div>
              <button type="button" @click="refreshCaptcha" style="margin-top:5px;">刷新验证码</button>
            </div>
            <button type="submit" class="submit-btn">
              <span>登录</span>
            </button>
          </form>
          <router-link to="/register" class="switch-link">
            没有账号？立即注册
          </router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'

const router = useRouter()
const showLogin = ref(true)
const loginForm = ref({
  name: '',
  password: ''
})
const emailForm = ref({
  email: '',
  code: ''
})
const errorMessage = ref('')

const captchaImg = ref('')
const captchaTargets = ref([])
const captchaId = ref('')
const captchaClicks = ref([])

const showAlert = ref(false);
function closeAlert() {
  showAlert.value = false;
  localStorage.removeItem('intrusion_alert');
}
onMounted(() => {
  localStorage.removeItem('intrusion_alert');
  fetchCaptcha()
})

const fetchCaptcha = async () => {
  const res = await axios.get('/api/click_captcha/', { withCredentials: true })
  captchaImg.value = res.data.image
  captchaTargets.value = res.data.targets
  captchaId.value = res.data.captcha_id
  captchaClicks.value = []
}
const refreshCaptcha = () => {
  fetchCaptcha()
}
const handleCaptchaClick = (e) => {
  if (captchaClicks.value.length >= 4) return
  const rect = e.target.getBoundingClientRect()
  const x = e.clientX - rect.left
  const y = e.clientY - rect.top
  captchaClicks.value.push({x: Math.round(x), y: Math.round(y)})
}

const handleLogin = async () => {
  errorMessage.value = ''
  if (captchaClicks.value.length !== 4) {
    alert('请依次点击4个目标文字')
    return
  }
  try {
    // 校验验证码
    const verifyRes = await axios.post(
      '/api/click_captcha/verify/',
      {
        captcha_id: captchaId.value,
        clicks: captchaClicks.value
      },
      { withCredentials: true }
    )
    if (verifyRes.data.msg !== 'success') {
      alert('验证码错误，请重试')
      fetchCaptcha()
      return
    }
    // 验证码通过后再登录
    const response = await axios.post('/api/login', {
      username: loginForm.value.name,
      password: loginForm.value.password
    })
    if (response.status === 200) {
      alert(response.data.msg || '登录成功')
      // 登录成功后写入localStorage并派发事件
      if (response.data.name) {
        localStorage.setItem('name', response.data.name);
        window.dispatchEvent(new CustomEvent('updateUserName', { detail: response.data.name }));
      }
      if (response.data.permission !== undefined) {
        localStorage.setItem('permission', response.data.permission);
        window.dispatchEvent(new CustomEvent('updateUserPermission', { detail: response.data.permission }));
      }
      // 跳转首页，无需reload
      router.push('/liveness')
    }
  } catch (error) {
    let msg = error.response?.data?.msg || error.message || '登录失败'
    errorMessage.value = msg
    alert(msg)
    fetchCaptcha()
  }
}

// 新增邮箱验证码校验逻辑
const sendCodeDisabled = ref(false)
const sendCodeTimer = ref(0)
const sendCodeText = ref('发送验证码')
let timer = null

const sendEmailCode = async () => {
  if (sendCodeDisabled.value) return
  if (captchaClicks.value.length !== 4) {
    alert('请依次点击4个目标文字')
    return
  }
  try {
    // 校验点选验证码
    const verifyRes = await axios.post(
      '/api/click_captcha/verify/',
      {
        captcha_id: captchaId.value,
        clicks: captchaClicks.value
      },
      { withCredentials: true }
    )
    if (verifyRes.data.msg !== 'success') {
      alert('验证码错误，请重试')
      fetchCaptcha()
      return
    }
    // 校验通过后发送邮箱验证码
    const res = await axios.post('/api/send_email_code', {
      email: emailForm.value.email
    }, { withCredentials: true })
    // alert(res.data.msg || '验证码已发送')  // 发送成功后不再弹窗
    // 启动倒计时
    sendCodeDisabled.value = true
    sendCodeTimer.value = 30
    sendCodeText.value = '30秒后可重发'
    timer = setInterval(() => {
      sendCodeTimer.value--
      sendCodeText.value = sendCodeTimer.value + '秒后可重发'
      if (sendCodeTimer.value <= 0) {
        clearInterval(timer)
        sendCodeDisabled.value = false
        sendCodeText.value = '发送验证码'
      }
    }, 1000)
  } catch (err) {
    let msg = err.response?.data?.msg || err.message || '发送失败'
    alert(msg)
    fetchCaptcha()
  }
}

const handleEmailLogin = async () => {
  if (!emailForm.value.email || !emailForm.value.code) {
    alert('请输入邮箱和验证码')
    return
  }
  if (captchaClicks.value.length !== 4) {
    alert('请依次点击4个目标文字')
    return
  }
  try {
    // 校验点选验证码
    const verifyRes = await axios.post(
      '/api/click_captcha/verify/',
      {
        captcha_id: captchaId.value,
        clicks: captchaClicks.value
      },
      { withCredentials: true }
    )
    if (verifyRes.data.msg !== 'success') {
      alert('验证码错误，请重试')
      fetchCaptcha()
      return
    }
    // 验证码通过后再邮箱登录
    const res = await axios.post('/api/email_login', {
      email: emailForm.value.email,
      code: emailForm.value.code
    }, { withCredentials: true })
    if (res.status === 200) {
      alert(res.data.msg || '登录成功')
      if (res.data.name) {
        localStorage.setItem('name', res.data.name);
        window.dispatchEvent(new CustomEvent('updateUserName', { detail: res.data.name }));
      }
      if (res.data.permission !== undefined) {
        localStorage.setItem('permission', res.data.permission);
        window.dispatchEvent(new CustomEvent('updateUserPermission', { detail: res.data.permission }));
      }
      localStorage.setItem('email', emailForm.value.email)
      // 邮箱验证码登录成功后也跳转到/liveness
      router.push('/liveness')
    }
  } catch (err) {
    let msg = err.response?.data?.msg || err.message || '登录失败'
    alert(msg)
    // 新增：如果是“用户不存在”，跳转注册并自动填邮箱
    if (msg === '用户不存在') {
      localStorage.setItem('register_email', emailForm.value.email)
      router.push('/register')
    }
    fetchCaptcha()
  }
}
onUnmounted(() => { if (timer) clearInterval(timer) })
</script>
  
  <style scoped>
.login-bg {
  position: fixed;
  left: 0; right: 0; top: 0; bottom: 0;
  width: 100vw;
  height: 100vh;
  overflow-y: auto;
  z-index: 0;
  background: url('@/assets/login-bg.gif') center center / cover no-repeat;
}
.login-bg::before {
  content: '';
  position: absolute;
  left: 0; right: 0; top: 0; bottom: 0;
  width: 100vw;
  height: 100vh;
  background: rgba(20, 30, 60, 0.38); /* 透明度更高 */
  z-index: 0;
}
.auth-container {
  position: relative;
  z-index: 1;
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
}
.auth-box {
  width: 100%;
  max-width: 420px;
  background: rgba(255,255,255,0.82); /* 透明度更高 */
  border-radius: 28px;
  box-shadow: 0 10px 40px rgba(0,0,0,0.22);
  padding: 48px 24px 32px 24px;
  margin: 32px 0;
  position: relative;
  z-index: 2;
  border: 2px solid #b6e6fa; /* 浅蓝色边框 */
}
.form-title {
  text-align: center;
  margin-bottom: 32px;
  color: #1a2236;
  font-size: 2.2rem;
  font-weight: 800;
  letter-spacing: 2px;
  text-shadow: 0 2px 8px rgba(0,0,0,0.06);
}
.form-group {
  margin-bottom: 22px;
}
.form-group label {
  display: block;
  margin-bottom: 7px;
  color: #3a466e;
  font-weight: 600;
  letter-spacing: 1px;
}
.form-group input {
  width: 100%;
  max-width: 100%;
  box-sizing: border-box;
  padding: 13px 14px;
  border: 1.5px solid #b6e6fa; /* 浅蓝色边框 */
  border-radius: 12px;
  font-size: 1.08rem;
  background: rgba(255,255,255,0.92); /* 透明度略提升 */
  box-shadow: 0 2px 8px rgba(30,40,90,0.04);
  transition: border 0.2s, box-shadow 0.2s;
}
.form-group input:focus {
  border-color: #00a1d6;
  outline: none;
  box-shadow: 0 0 0 2px #b6e6fa;
}
.submit-btn {
  width: 100%;
  background: linear-gradient(90deg,#00a1d6 0%,#00c6fb 100%);
  color: white;
  padding: 15px 0;
  border: none;
  border-radius: 16px;
  cursor: pointer;
  font-size: 1.18rem;
  font-weight: bold;
  transition: background 0.2s, box-shadow 0.2s;
  margin-top: 12px;
  box-shadow: 0 4px 16px rgba(0,161,214,0.10);
  letter-spacing: 2px;
}
.submit-btn:hover {
  background: linear-gradient(90deg,#00b5e5 0%,#00a1d6 100%);
  box-shadow: 0 6px 24px rgba(0,161,214,0.18);
}
.switch-link {
  color: #00a1d6;
  cursor: pointer;
  font-size: 1.01rem;
  display: block;
  text-align: center;
  margin-top: 20px;
  text-decoration: underline;
  font-weight: 500;
}
.auth-box button {
  border: none;
  background: #f3f7fa;
  color: #1a2236;
  font-size: 1.05rem;
  padding: 8px 22px;
  border-radius: 12px;
  margin-bottom: 0;
  font-weight: 600;
  transition: background 0.18s, color 0.18s;
  box-shadow: 0 1px 4px rgba(0,0,0,0.04);
}
.auth-box button.active,
.auth-box button:focus {
  background: #00a1d6;
  color: #fff;
}
.auth-box button:not(.active):hover {
  background: #e6f7fd;
  color: #00a1d6;
}
.form-group > div[style*='position:relative'] {
  border-radius: 10px;
  border: 1.5px solid #b6e6fa !important; /* 浅蓝色边框 */
  background: #f8fafc;
  box-shadow: 0 2px 8px rgba(30,40,90,0.04);
}
.form-group button[type='button'] {
  background: #f3f7fa;
  color: #00a1d6;
  border: none;
  border-radius: 8px;
  padding: 6px 18px;
  font-size: 1rem;
  margin-top: 6px;
  margin-left: 0;
  font-weight: 600;
  transition: background 0.18s, color 0.18s;
}
.form-group button[type='button']:hover {
  background: #e6f7fd;
  color: #00a1d6;
}
.big-alert-overlay {
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(255,0,0,0.7);
  z-index: 9999;
  display: flex;
  align-items: center;
  justify-content: center;
}
.big-alert-box {
  background: #fff;
  border: 6px solid #ff0000;
  border-radius: 24px;
  padding: 80px 120px;
  text-align: center;
  box-shadow: 0 0 60px #ff0000;
}
.big-alert-box h1 {
  color: #ff0000;
  font-size: 3.5em;
  margin-bottom: 40px;
}
.big-alert-box button {
  font-size: 2em;
  padding: 16px 60px;
  border: none;
  border-radius: 12px;
  background: #ff0000;
  color: #fff;
  cursor: pointer;
}
/* 验证码输入区域横向排列 */
.form-group-code {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 22px;
}
.code-label {
  flex: 0 0 auto;
  margin-bottom: 0;
  color: #3a466e;
  font-weight: 600;
  letter-spacing: 1px;
  white-space: nowrap;
}
.code-input {
  flex: 1 1 0;
  margin-bottom: 0;
}
.code-btn {
  background: #f3f7fa;
  color: #00a1d6;
  border: none;
  border-radius: 8px;
  padding: 6px 18px;
  font-size: 1rem;
  font-weight: 600;
  transition: background 0.18s, color 0.18s;
  margin-left: 0;
  margin-bottom: 0;
  box-shadow: 0 1px 4px rgba(0,0,0,0.04);
}
.code-btn:hover {
  background: #e6f7fd;
  color: #00a1d6;
}
  </style>