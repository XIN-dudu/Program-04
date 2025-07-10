//控制页面直接的跳转
// src/router/index.js
import { createRouter, createWebHistory, useRouter } from 'vue-router'

const routes = [
  { path: '/', component: () => import('../views/Login.vue') },
  { path: '/home', component: () => import('../views/Info.vue'), meta: { requiresAuth: true } },
  { path: '/monitor', component: () => import('../views/MonitorRoad.vue'), meta: { requiresAuth: true } },
  {
    path: '/urbanTraffic',
    component: () => import('@/views/UrbanTraffic.vue'),
    children: [
      {
        path: 'trajectory',
        component: () => import('@/views/urbanTraffic/Trajectory.vue')
      },
      {
        path: 'hotspot',
        component: () => import('@/views/urbanTraffic/Hotspot.vue')
      },
      {
        path: 'weekflow',
        component: () => import('@/views/urbanTraffic/Weekflow.vue')
      },
      {
        path: 'road',
        component: () => import('@/views/urbanTraffic/Road.vue')
      }
    ]
  },
  { path: '/history', component: () => import('../views/History.vue'), meta: { requiresAuth: true } },
  { path: '/login', component: () => import('../views/Login.vue') },
  { path: '/register', component: () => import('../views/Register.vue') },
  { path: '/face-recognition', component: () => import('../views/FaceRecognition.vue'), meta: { requiresAuth: true } },
  { path: '/liveness', component: () => import('../views/LivenessDetection.vue'), meta: { requiresAuth: true } },
  {
    path: '/user-manage',
    name: 'UserManage',
    component: () => import('@/views/UserManage.vue')
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫
router.beforeEach((to, from, next) => {
  const isLoggedIn = localStorage.getItem('name') || localStorage.getItem('email')
  
  if (to.meta.requiresAuth && !isLoggedIn) {
    // 需要登录但未登录，重定向到登录页
    next('/')
  } else if (to.path === '/' && isLoggedIn) {
    // 已登录但访问登录页，重定向到首页
    next('/home')
  } else if (to.name === 'UserManage' && localStorage.getItem('permission') != '2') {
    next('/')
  } else {
    next()
  }
})

export default router