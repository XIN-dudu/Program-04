<!-- src/App.vue 主窗口 -->
<template>
  <div id="app" class="bilibili-layout">
    <!-- 顶部导航栏 -->
    <header class="nav-header">
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
        <div>
          <router-link to="/history" class="logo-text">历史回放</router-link>
        </div>
        <div>
          <router-link to="/face-recognition" class="logo-text">人脸识别</router-link>
        </div>
        <div>
          <router-link to="/login" class="logo-text">登录</router-link>
        </div>
      </div>
    </header>

    <!-- 主体内容区域 -->
    <div>
      <main>
        <router-view />
      </main>
    </div>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router';
 
const router = useRouter();

</script>

<style scoped>
/* 基础布局样式 */
.bilibili-layout {
  min-height: 100vh;
  background: #f4f4f4;
}

.nav-header {
  background: #fff;
  box-shadow: 0 2px 4px rgba(0, 0, 0, .1);
  position: sticky;
  top: 0;
  z-index: 1000;
}

.header-container {
  display: flex;
  align-items: center;
  max-width: 1280px;
  margin: 0 auto;
  padding: 0 20px;
  height: 64px;
  gap: 20px;
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

.logo-text {
  font-size: 1.5rem;
  color: #00a1d6;
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
  min-height: calc(100vh - 124px);
}

/* 响应式适配 */
@media (max-width: 768px) {
  .header-container {
    flex-wrap: wrap;
    gap: 10px;
    height: auto;
    padding: 10px 20px;
  }

  .search-section {
    order: 3;
    flex-basis: 100%;
    margin-top: 10px;
  }

  .right-actions {
    margin-left: auto;
  }
}
</style>