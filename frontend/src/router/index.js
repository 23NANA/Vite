import { createRouter, createWebHistory } from 'vue-router'
import { getToken } from '@/utils/auth'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    { path: '/', redirect: '/manager/home' },
    {
      path: '/manager',
      name: 'Layout',
      redirect: '/manager/home',
      component: () => import('@/layouts/Layout.vue'),
      children: [
        { path: 'home', name: 'Home', component: () => import('@/views/Home.vue') },
        { path: 'lab', name: 'Lab', component: () => import('@/views/Lab.vue') },
        { path: 'equipment', name: 'Equipment', component: () => import('@/views/Equipment.vue') },
        { path: 'profile', name: 'Profile', component: () => import('@/views/Profile.vue') },
        { path: 'password', name: 'Password', component: () => import('@/views/Password.vue') },
        { path: 'user', name: 'User', component: () => import('@/views/User.vue') },
        { path: 'lablist', name: 'LabList', component: () => import('@/views/LabList.vue') },
        {
          path: 'lab-equipment',
          name: 'LabEquipment',
          component: () => import('@/views/LabEquipment.vue')
        },
        {
          path: 'my-reservation',
          name: 'MyReservation',
          component: () => import('@/views/MyReservation.vue')
        },
        {
          path: 'audit-reservation',
          name: 'AuditReservation',
          component: () => import('@/views/AuditReservation.vue')
        },

        // 放在最后：/manager 下未定义的路径也走 404，但保留左侧菜单
        {
          path: ':pathMatch(.*)*',
          name: 'ManagerNotFound',
          component: () => import('@/views/NotFound.vue')
        },
        {
          path: 'ai-chat',
          name: 'AIChat',
          component: () => import('@/views/AIChat.vue')
        }
      ]
    },
    { path: '/login', name: 'Login', component: () => import('@/views/Login.vue') },
    { path: '/register', name: 'Register', component: () => import('@/views/Register.vue') },
    // 兜底：匹配所有未定义路径，必须放在最后
    {
      path: '/:pathMatch(.*)*',
      name: 'NotFound',
      component: () => import('@/views/NotFound.vue')
    }

  ]
})

router.beforeEach((to, from) => {
  const token = getToken()

  if (to.path === '/login' || to.path === '/register') {
    return true
  } else {
    return token ? true : '/login'
  }
})


export default router