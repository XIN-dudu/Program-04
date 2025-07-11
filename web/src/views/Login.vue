<!-- 登录 -->
<!-- src/views/Login.vue -->
<template>
  <div class="login-bg">
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
            <div class="form-group" style="display:flex;align-items:center;">
              <label style="flex:0 0 60px;">验证码：</label>
              <input v-model="emailForm.code" type="text" required placeholder="请输入验证码" style="flex:1;">
              <button type="button" @click="handleSendEmailCode" style="margin-left:10px;">获取验证码</button>
            </div>
            <!-- 点选验证码区域（与账号密码登录共用） -->
            <div class="form-group" v-if="captchaImg">
              <label>请依次点击下列文字：</label>
              <span style="color:#d9534f;font-weight:bold;">{{ captchaTargets.join('、') }}</span>
              <div style="margin:10px 0;position:relative;width:320px;height:100px;border:1px solid #ccc;">
                <img :src="'data:image/png;base64,'+captchaImg" @click="handleCaptchaClick" style="width:320px;height:100px;cursor:pointer;"/>
                <span v-for="(pt, idx) in captchaClicks" :key="'email-'+idx" :style="{position:'absolute',left:pt.x-10+'px',top:pt.y-10+'px',width:'20px',height:'20px',background:'#00a1d6',color:'#fff',borderRadius:'50%',textAlign:'center',lineHeight:'20px',fontSize:'14px',pointerEvents:'none'}">{{ idx+1 }}</span>
              </div>
              <button type="button" @click="refreshCaptcha" style="margin-top:5px;">刷新验证码</button>
            </div>
            <button type="submit" class="submit-btn">
              <span>登录</span>
            </button>
          </form>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
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
onMounted(() => {
  fetchCaptcha()
})

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
      // 登录成功后
      if (response.data.name) {
        window.dispatchEvent(new CustomEvent('updateUserName', { detail: response.data.name }));
        window.location.reload();
      }
      if (response.data.permission !== undefined) {
        window.dispatchEvent(new CustomEvent('updateUserPermission', { detail: response.data.permission }));
      }
      router.push('/home')
    }
  } catch (error) {
    let msg = error.response?.data?.msg || error.message || '登录失败'
    errorMessage.value = msg
    alert(msg)
    fetchCaptcha()
  }
}

// 新增邮箱验证码校验逻辑
const handleSendEmailCode = async () => {
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
    // 验证码通过后再发送邮箱验证码
    const res = await axios.post('/api/send_email_code', {
      email: emailForm.value.email
    }, { withCredentials: true })
    alert(res.data.msg || '验证码已发送')
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
      localStorage.setItem('email', emailForm.value.email)
      // 登录成功后
      if (res.data.name) {
        window.dispatchEvent(new CustomEvent('updateUserName', { detail: res.data.name }));
        window.location.reload();
      }
      if (res.data.permission !== undefined) {
        window.dispatchEvent(new CustomEvent('updateUserPermission', { detail: res.data.permission }));
      }
      router.push('/home')
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
</script>
  
  <style scoped>
.login-bg {
  position: fixed;
  left: 0; right: 0; top: 0; bottom: 0;
  width: 100vw;
  height: 100vh;
  overflow-y: auto; /* 增加垂直滚动条 */
  z-index: 0;
  background: url('@/assets/login-bg.gif') center center / cover no-repeat;
  /* 去除模糊和亮度调整 */
}
.bg-video {
  display: none;
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
  max-width: 440px;
  background: rgba(255,255,255,0.85); /* 提高透明度，去除磨砂 */
  border-radius: 24px;
  box-shadow: 0 8px 32px rgba(0,0,0,0.18);
  padding: 48px 16px 32px 16px;
  /* 去除backdrop-filter */
}
.form-title {
  text-align: center;
  margin-bottom: 30px;
  color: #222;
  font-size: 2rem;
  font-weight: bold;
  letter-spacing: 2px;
}
.form-group {
  margin-bottom: 20px;
}
.form-group label {
  display: block;
  margin-bottom: 5px;
  color: #666;
}
.form-group input {
  width: 100%;
  max-width: 100%;
  box-sizing: border-box;
  padding: 12px;
  border: 1px solid #ddd;
  border-radius: 8px;
  font-size: 1.1rem;
  background: rgba(255,255,255,0.9);
}
.form-group input:focus {
  border-color: #00a1d6;
  outline: none;
}
.submit-btn {
  width: 100%;
  background: #00a1d6;
  color: white;
  padding: 14px;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 1.1rem;
  font-weight: bold;
  transition: background 0.2s;
  margin-top: 10px;
}
.submit-btn:hover {
  background: #00b5e5;
}
.switch-link {
  color: #00a1d6;
  cursor: pointer;
  font-size: 1rem;
  display: block;
  text-align: center;
  margin-top: 18px;
}
  </style>