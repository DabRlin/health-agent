import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/Login.vue'),
    meta: { title: '登录', public: true }
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('../views/Register.vue'),
    meta: { title: '注册', public: true }
  },
  {
    path: '/',
    name: 'Home',
    component: () => import('../views/Home.vue'),
    meta: { title: '首页' }
  },
  {
    path: '/consultation',
    name: 'Consultation',
    component: () => import('../views/Consultation.vue'),
    meta: { title: '智能问诊' }
  },
  {
    path: '/health-data',
    name: 'HealthData',
    component: () => import('../views/HealthData.vue'),
    meta: { title: '健康数据' }
  },
  {
    path: '/risk-assessment',
    name: 'RiskAssessment',
    component: () => import('../views/RiskAssessment.vue'),
    meta: { title: '风险评估' }
  },
  {
    path: '/profile',
    name: 'Profile',
    component: () => import('../views/Profile.vue'),
    meta: { title: '健康档案' }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  document.title = `${to.meta.title || 'HealthAI'} - HealthAI`
  
  // 检查登录状态 - 统一使用 token 判断
  const token = localStorage.getItem('token')
  const isLoggedIn = !!token
  
  // 如果是公开页面，直接放行
  if (to.meta.public) {
    // 已登录用户访问登录/注册页，跳转首页
    if ((to.name === 'Login' || to.name === 'Register') && isLoggedIn) {
      next({ name: 'Home' })
    } else {
      next()
    }
    return
  }
  
  // 未登录跳转登录页
  if (!isLoggedIn) {
    next({ name: 'Login' })
    return
  }
  
  next()
})

export default router
