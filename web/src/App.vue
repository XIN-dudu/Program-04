<!-- src/App.vue 主窗口 -->
<template>
  <div id="app" class="bilibili-layout">
    <!-- 顶部导航栏 - 只在已登录且不是登录/注册页时显示 -->
    <header v-if="showNav" class="nav-header">
      <div class="header-container">
        <div>
          <router-link to="/home" class="logo-text">首页</router-link>
        </div>
        <div>
          <router-link to="/monitor" class="logo-text">智能检测</router-link>
        </div>
        <div>
          <router-link to="/urbanTraffic" class="logo-text">城市交通</router-link>
        </div>
        <div v-if="isAdmin">
          <router-link to="/history" class="logo-text">历史回放</router-link>
        </div>
        <div v-if="isAdmin">
          <router-link to="/systemlog" class="logo-text">系统日志</router-link>
        </div>
        <div class="user-section">
          <router-link v-if="isAdmin" to="/user-manage" class="logo-text" style="margin-right:18px;">用户管理</router-link>
          <router-link v-if="isAdmin" to="/maintaince" class="logo-text" style="margin-right:18px;">维修分配</router-link>
          <!-- 管理员入侵告警铃铛 -->
          <div v-if="isAdmin" class="nav-bell" @click="showAlertDialog = true">
            <svg class="bell-icon" viewBox="0 0 24 24"><path d="M12 2C9.243 2 7 4.243 7 7v2.382C7 10.271 6.632 11.104 6.025 11.707L4.293 13.439A.997.997 0 0 0 4 14.172V17a1 1 0 0 0 1 1h14a1 1 0 0 0 1-1v-2.828a.997.997 0 0 0-.293-.733l-1.732-1.732A2.997 2.997 0 0 1 17 9.382V7c0-2.757-2.243-5-5-5zm0 18c-1.104 0-2-.896-2-2h4c0 1.104-.896 2-2 2z"/></svg>
            <span v-if="hasIntrusionAlert" class="red-dot"></span>
          </div>
          <router-link to="/profile" class="username clickable">{{ username }}</router-link>
          <button @click="logout" class="logout-btn">退出</button>
          <router-link v-if="isRepairMan" to="/repair" class="logo-text" style="margin-right:18px;">维修任务</router-link>
        </div>
      </div>
    </header>
    <!-- 主体内容区域 -->
    <div>
      <main>
        <router-view />
      </main>
    </div>
    <!-- 全局入侵者弹窗 -->
    <div v-if="showAlertDialog" class="global-alert-dialog-mask">
      <div class="global-alert-dialog-box">
        <h1 style="color:#e53935;font-size:2.3rem;">检测到入侵者</h1>
        <div style="font-size:1.25rem;margin:22px 0;">请及时查看系统日志！</div>
        <button class="global-alert-close" @click="closeAlertDialog">我知道了</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import axios from 'axios';
 
const router = useRouter();
const route = useRoute();

watch(
  () => route.path,
  () => {
    userNameRef.value = localStorage.getItem('name') || '用户';
    userPermissionRef.value = localStorage.getItem('permission') || '0';
  }
);

const isLoggedIn = computed(() => {
  return !!(userNameRef.value && userNameRef.value !== '用户');
});

const showNav = computed(() => {
  const path = route.path;
  // 首页/、登录、注册、身份认证页面都不显示导航栏
  return !['/', '/login', '/register', '/liveness'].includes(path);
});

const userNameRef = ref(localStorage.getItem('name') || '用户');
function updateUserName(name) {
  localStorage.setItem('name', name);
  userNameRef.value = name;
}
onMounted(() => {
  window.addEventListener('updateUserName', (e) => {
    updateUserName(e.detail);
  });
  window.addEventListener('storage', () => {
    userNameRef.value = localStorage.getItem('name') || '用户';
  });
});
onUnmounted(() => {
  window.removeEventListener('updateUserName', updateUserName);
});
const username = computed(() => userNameRef.value);

const userPermissionRef = ref(localStorage.getItem('permission') || '0');
function updateUserPermission(permission) {
  localStorage.setItem('permission', permission);
  userPermissionRef.value = permission;
}
onMounted(() => {
  window.addEventListener('updateUserPermission', (e) => {
    updateUserPermission(e.detail);
  });
  window.addEventListener('storage', () => {
    userPermissionRef.value = localStorage.getItem('permission') || '0';
  });
});
onUnmounted(() => {
  window.removeEventListener('updateUserPermission', updateUserPermission);
});
const isAdmin = computed(() => userPermissionRef.value == '2');
const isRepairMan = computed(() => userPermissionRef.value == '1');

// 入侵告警全局铃铛和弹窗
import { onBeforeUnmount } from 'vue';
const hasIntrusionAlert = ref(false);
const showAlertDialog = ref(false);
let lastIntrusionId = null;
let pollTimer = null;
function closeAlertDialog() {
  showAlertDialog.value = false;
  hasIntrusionAlert.value = false;
}
async function pollIntrusionLog() {
  try {
    const res = await axios.get('/api/logs/', {
      params: { level: 'warning', action: '入侵者告警' },
      withCredentials: true
    });
    if (res.data && res.data.length > 0) {
      const latest = res.data[0];
      if (!lastIntrusionId || latest.id !== lastIntrusionId) {
        hasIntrusionAlert.value = true;
        showAlertDialog.value = true;
        lastIntrusionId = latest.id;
      }
    }
  } catch {}
}
onMounted(() => {
  if (isAdmin.value) {
    pollIntrusionLog();
    pollTimer = setInterval(pollIntrusionLog, 30000);
  }
});
onBeforeUnmount(() => {
  if (pollTimer) clearInterval(pollTimer);
});

const logout = () => {
  localStorage.removeItem('name');
  localStorage.removeItem('email');
  router.push('/');
};
</script>

<style scoped>
/* 基础布局样式 */
.bilibili-layout {
  min-height: 100vh;
  background: #f4f4f4;
}

/* Mac风格导航栏美化 */
.nav-header {
  background: rgba(255,255,255,0.85);
  box-shadow: 0 4px 16px rgba(0,0,0,0.07);
  border-radius: 18px;
  margin: 18px auto 32px auto;
  max-width: 1400px;
  position: sticky;
  top: 0;
  z-index: 1000;
  padding: 0 24px;
  height: 64px;
  display: flex;
  align-items: center;
}
.header-container {
  display: flex;
  align-items: center;
  width: 100%;
  height: 64px;
  gap: 32px;
}
.logo-text {
  font-size: 1.25rem;
  color: #007aff;
  font-weight: 500;
  text-decoration: none;
  padding: 6px 18px;
  border-radius: 12px;
  transition: background 0.2s, color 0.2s;
  letter-spacing: 1px;
}
.logo-text:hover {
  background: #f2f6fa;
  color: #0051a8;
}
.router-link-exact-active.logo-text {
  background: #eaf3ff;
  color: #0051a8;
  font-weight: 600;
}
.user-section {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-left: auto;
}
.username {
  color: #444;
  font-size: 1.08rem;
  font-weight: 500;
  background: #f5f6fa;
  border-radius: 12px;
  padding: 6px 18px;
  margin-right: 8px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.04);
  transition: background 0.2s;
}
.username.clickable {
  cursor: pointer;
  text-decoration: underline dotted #b0b0b0 1.5px;
}
.logout-btn {
  padding: 6px 18px;
  background: linear-gradient(90deg,#ff7e5f,#feb47b);
  color: white;
  border: none;
  border-radius: 12px;
  cursor: pointer;
  font-size: 1rem;
  font-weight: 500;
  box-shadow: 0 2px 8px rgba(255,126,95,0.08);
  transition: background 0.2s;
}
.logout-btn:hover {
  background: linear-gradient(90deg,#ff6a4d,#ffb88c);
}
@media (max-width: 900px) {
  .nav-header { max-width: 100vw; border-radius: 0; margin: 0 0 18px 0; }
  .header-container { gap: 10px; }
  .logo-text { font-size: 1rem; padding: 4px 10px; }
  .username { padding: 4px 10px; }
  .logout-btn { padding: 4px 10px; font-size: 0.95rem; }
}

/* 左侧Logo区 */
.logo-section {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.bilibili-logo {
  display: flex;
  align-items: center;
  gap: 4px;
  color: #00a1d6;
  font-weight: bold;
  font-size: 1.25rem;
}

.bilibili-logo img {
  height: 36px;
}

/* 用户区域 */
.user-section {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-left: auto;
}

.username {
  color: #666;
  font-size: 1rem;
}

.username.clickable {
  cursor: pointer;
  text-decoration: underline;
}

.logout-btn {
  padding: 6px 12px;
  background: #ff6b6b;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.9rem;
  transition: background 0.2s;
}

.logout-btn:hover {
  background: #ff5252;
}

/* 搜索栏 */
.search-section {
  flex-grow: 1;
  min-width: 0;
  /* 防止内容溢出 */
}

.search-box {
  position: relative;
  width: 100%;
  max-width: 600px;
  margin: 0 auto;
}

.search-box input {
  width: 100%;
  padding: 8px 40px 8px 15px;
  border: 1px solid #ccd0d7;
  border-radius: 32px;
  font-size: 1rem;
  background: #f4f4f4;
  transition: all 0.2s;
}

.search-box input:focus {
  background: #fff;
  border-color: #00a1d6;
  outline: none;
}

.search-btn {
  position: absolute;
  right: 8px;
  top: 50%;
  transform: translateY(-50%);
  padding: 5px;
  background: none;
  border: none;
  cursor: pointer;
}

.search-btn .icon {
  width: 20px;
  height: 20px;
  fill: #999;
}

/* 右侧功能按钮 */
.right-actions {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-left: 20px;
  flex-shrink: 0;
}

.action-btn {
  padding: 8px 20px;
  border-radius: 8px;
  font-size: 1rem;
  transition: all 0.2s;
  white-space: nowrap;
}

.upload-btn {
  background: #00a1d6;
  color: white;
}

.upload-btn:hover {
  background: #00b5e5;
}

.login-btn {
  background: #fff;
  color: #00a1d6;
  border: 1px solid #00a1d6;
}

.login-btn:hover {
  background: #00a1d6;
  color: white;
}

.account-btn {
  background: #fff;
  color: #00a1d6;
  border: 1px solid #00a1d6;
}

.account-btn:hover {
  background: #00a1d6;
  color: white;
}

/* 主体内容布局 */
.main-container {
  max-width: 1280px;
  margin: 20px auto;
  padding: 0 20px;
}

.content-area {
  background: #fff;
  border-radius: 8px;
  padding: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, .1);
}

.edit-modal {
  position: fixed;
  left: 0; right: 0; top: 0; bottom: 0;
  background: rgba(0,0,0,0.2);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
}
.edit-modal-content {
  background: #fff;
  border-radius: 8px;
  padding: 24px;
  min-width: 320px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.15);
}
.edit-modal-content h3 {
  margin-top: 0;
  margin-bottom: 18px;
  font-size: 1.2rem;
  color: #222;
}
.edit-modal-content .form-group {
  margin-bottom: 16px;
}
.edit-modal-content label {
  display: block;
  margin-bottom: 6px;
  color: #666;
}
.edit-modal-content input {
  width: 100%;
  padding: 8px;
  border: 1px solid #ccc;
  border-radius: 4px;
  font-size: 1rem;
  box-sizing: border-box;
}
.nav-bell {
  position: relative;
  margin-right: 18px;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 38px;
  height: 38px;
  background: #fff6f6;
  border-radius: 50%;
  box-shadow: 0 2px 8px rgba(229,57,53,0.08);
  transition: box-shadow 0.18s;
}
.nav-bell:hover {
  box-shadow: 0 4px 16px rgba(229,57,53,0.18);
  background: #ffeaea;
}
.bell-icon {
  width: 28px;
  height: 28px;
  fill: #e53935;
  filter: drop-shadow(0 0 2px #fff3f3);
}
.red-dot {
  position: absolute;
  top: 7px;
  right: 7px;
  width: 13px;
  height: 13px;
  background: #e53935;
  border-radius: 50%;
  border: 2px solid #fff;
  box-shadow: 0 0 6px #e53935;
  z-index: 2;
}
.global-alert-dialog-mask {
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(255,0,0,0.13);
  z-index: 9999;
  display: flex;
  align-items: center;
  justify-content: center;
}
.global-alert-dialog-box {
  background: #fff;
  border-radius: 32px;
  box-shadow: 0 16px 64px rgba(255,0,0,0.18), 0 3px 12px rgba(30,40,90,0.10);
  padding: 64px 80px;
  text-align: center;
  min-width: 520px;
  min-height: 320px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}
.global-alert-close {
  margin-top: 32px;
  background: #e53935;
  color: #fff;
  border: none;
  border-radius: 12px;
  padding: 16px 48px;
  font-size: 1.5rem;
  font-weight: 700;
  cursor: pointer;
  box-shadow: 0 2px 8px rgba(229,57,53,0.12);
  transition: background 0.18s;
}
.global-alert-close:hover {
  background: #b71c1c;
}
</style>