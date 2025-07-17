<template>
  <div class="info-container">
    <h1>欢迎使用 <span class="highlight">道路病害管理系统</span></h1>
    <p class="subtext">智能检测 · 精准分配 · 高效维修</p>
    <div class="user-info-mac">
      <img class="user-avatar-mac" :src="avatarUrl" alt="avatar" />
      <span class="user-label-mac">当前用户</span>
      <span class="user-name-mac">{{ username }}</span>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'

const username = ref('')
const avatarUrl = ref(require('@/assets/default-avatar.png'))

onMounted(() => {
  username.value = localStorage.getItem('name') || '游客'
  // 优先用 /api/avatar/用户名/ 作为头像
  if (username.value && username.value !== '游客') {
    const API_BASE = process.env.VUE_APP_API_BASE || ''
    avatarUrl.value = API_BASE + '/api/avatar/' + username.value + '/'
  } else {
    avatarUrl.value = require('@/assets/default-avatar.png')
  }
})
</script>

<style scoped>
.info-container {
  max-width: 800px;
  margin: 80px auto;
  padding: 50px 30px;
  text-align: center;
  background: linear-gradient(to bottom right, #ffffff, #f0f4f8);
  border-radius: 20px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.08);
  font-family: "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
}

h1 {
  font-size: 36px;
  margin-bottom: 20px;
  color: #2c3e50;
}

.highlight {
  color: #007bff;
}

.subtext {
  font-size: 18px;
  color: #555;
  margin-bottom: 40px;
  letter-spacing: 1px;
}

.user-info-mac {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 18px;
  background: rgba(245, 247, 250, 0.95);
  border-radius: 18px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
  padding: 14px 32px 14px 20px;
  margin: 0 auto;
  width: fit-content;
  font-size: 18px;
}
.user-avatar-mac {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  box-shadow: 0 2px 8px rgba(0,0,0,0.08);
  border: 2px solid #e6f0ff;
  background: #fff;
}
.user-label-mac {
  color: #888;
  font-size: 16px;
  margin-right: 6px;
  letter-spacing: 1px;
}
.user-name-mac {
  color: #007aff;
  font-size: 20px;
  font-weight: 600;
  background: #eaf3ff;
  border-radius: 10px;
  padding: 4px 18px;
  margin-left: 2px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.04);
  letter-spacing: 1px;
}
</style>
