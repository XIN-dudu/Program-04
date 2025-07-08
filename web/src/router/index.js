//控制页面直接的跳转
// src/router/index.js
import { createRouter, createWebHistory, useRouter } from 'vue-router'

const routes = [
  { path: '/', redirect: '/home' },
  { path: '/home', component: () => import('../views/Info.vue') },
  { path: '/monitor', component: () => import('../views/MonitorRoad.vue') },
  { path: '/urbanTraffic', component: () => import('../views/UrbanTraffic.vue') },
  { path: '/history', component: () => import('../views/History.vue') },
  { path: '/login', component: () => import('../views/Login.vue') },
  { path: '/register', component: () => import('../views/Register.vue') },
]
const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router