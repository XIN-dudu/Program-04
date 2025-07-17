<template>
  <div class="info-container">
    <h1>欢迎使用 <span class="highlight">道路病害管理系统</span></h1>
    <p class="subtext">智能检测 · 精准分配 · 高效维修</p>
    <div class="user-info">
      当前用户：<strong>{{ username }}</strong>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'

const username = ref('')

onMounted(() => {
  username.value = localStorage.getItem('name') || '游客'
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

.user-info {
  font-size: 16px;
  color: #444;
  background-color: #e6f0ff;
  padding: 10px 20px;
  border-radius: 12px;
  display: inline-block;
}
</style>
