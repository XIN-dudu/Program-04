<!-- 登录 -->
<!-- src/views/Login.vue -->
<template>
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
  const res = await axios.get('http://localhost:8000/click_captcha/', { withCredentials: true })
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
      'http://localhost:8000/click_captcha/verify/',
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
    const response = await axios.post('http://localhost:8000/login', {
      username: loginForm.value.name,
      password: loginForm.value.password
    })
    if (response.status === 200) {
      alert(response.data.msg || '登录成功')
      localStorage.setItem('name', loginForm.value.name)
      router.push('/')
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
      'http://localhost:8000/click_captcha/verify/',
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
    const res = await axios.post('http://localhost:8000/send_email_code', {
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
      'http://localhost:8000/click_captcha/verify/',
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
    const res = await axios.post('http://localhost:8000/email_login', {
      email: emailForm.value.email,
      code: emailForm.value.code
    }, { withCredentials: true })
    if (res.status === 200) {
      alert(res.data.msg || '登录成功')
      localStorage.setItem('email', emailForm.value.email)
      router.push('/')
    }
  } catch (err) {
    let msg = err.response?.data?.msg || err.message || '登录失败'
    alert(msg)
    fetchCaptcha()
  }
}
</script>
  
  <style scoped>
  .auth-container {
    display: flex;
    justify-content: center;
    align-items: center;
    min-height: calc(100vh - 124px);
    background: #f4f4f4;
  }
  
  .auth-box {
    width: 100%;
    max-width: 400px;
    background: white;
    border-radius: 8px;
    box-shadow: 0 2px 10px rgba(0,0,0,.1);
    padding: 40px;
  }
  
  .form-title {
    text-align: center;
    margin-bottom: 30px;
    color: #222;
    font-size: 1.5rem;
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
    padding: 10px;
    border: 1px solid #ddd;
    border-radius: 4px;
    font-size: 1rem;
  }
  
  .form-group input:focus {
    border-color: #00a1d6;
    outline: none;
  }
  
  .submit-btn {
    width: 100%;
    background: #00a1d6;
    color: white;
    padding: 12px;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-size: 1rem;
    transition: background 0.2s;
  }
  
  .submit-btn:hover {
    background: #00b5e5;
  }
  
  .form-footer {
    text-align: center;
    margin-top: 20px;
  }
  
  .switch-link {
    color: #00a1d6;
    cursor: pointer;
    font-size: 0.9rem;
  }
  
  .switch-link:hover {
    text-decoration: underline;
  }
  
  /* 注册表单样式调整 */
  .register-form {
    display: none;
  }
  
  </style>