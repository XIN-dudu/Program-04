//控制页面直接的跳转
// src/router/index.js
import { createRouter, createWebHistory, useRouter } from 'vue-router'
import axios from 'axios'

const routes = [
  { path: '/', component: () => import('../views/Login.vue') },
  { path: '/home', component: () => import('../views/Info.vue'), meta: { requiresAuth: true } },
  { path: '/monitor', component: () => import('../views/MonitorRoad.vue'), meta: { requiresAuth: true } },
  { path: '/maintaince', component: () => import('../views/Maintaince.vue'), meta: { requiresAuth: true } },
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
        path: 'shandongmap',
        component: () => import('@/views/urbanTraffic/ShandongMap.vue')
      }
      // 已删除 weekflow 和 road 路由
    ]
  },
  { path: '/history', component: () => import('../views/History.vue'), meta: { requiresAuth: true } },
  { path: '/login', component: () => import('../views/Login.vue') },
  { path: '/repair', component: () => import('../views/Repair.vue') },
  { path: '/register', component: () => import('../views/Register.vue') },
  { path: '/face-recognition', component: () => import('../views/FaceRecognition.vue'), meta: { requiresAuth: true } },
  { path: '/liveness', component: () => import('../views/LivenessDetection.vue'), meta: { requiresAuth: true } },
  { path: '/profile', component: () => import('../views/UserProfile.vue'), meta: { requiresAuth: true } },
  { path: '/systemlog', component: () => import('../views/SystemLog.vue'), meta: { requiresAuth: true } },  
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
router.beforeEach(async (to, from, next) => {
  // 登录页和注册页不需要校验
  if (to.path === '/login' || to.path === '/register') {
    return next();
  }
  // 需要登录的页面
  if (to.meta.requiresAuth) {
    try {
      const res = await axios.get('/api/user/profile/', { withCredentials: true });
      if (res.status === 200 && res.data && res.data.username) {
        next(); // 已登录
      } else {
        next('/login'); // 未登录
      }
    } catch (e) {
      // 401或其他错误都跳转到登录页
      next('/login');
    }
  } else if (to.name === 'UserManage' && localStorage.getItem('permission') != '2') {
    next('/');
  } else {
    next();
  }
});

export default router