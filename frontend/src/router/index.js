import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/', name: 'Home', component: () => import('../views/HomeView.vue') },
  { path: '/work', name: 'WorkList', component: () => import('../views/WorkListView.vue') },
  { path: '/space', name: 'SpaceList', component: () => import('../views/SpaceListView.vue') },
  { path: '/works/:slug', name: 'WorkDetail', component: () => import('../views/WorkDetail.vue') },
  { path: '/contact', name: 'Contact', component: () => import('../views/ContactView.vue') },
  { path: '/about', name: 'About', component: () => import('../views/AboutView.vue') },
  // 后台
  { path: '/login', name: 'Login', component: () => import('../views/LoginView.vue') },
  {
    path: '/admin',
    name: 'Admin',
    component: () => import('../views/AdminDashboard.vue'),
    meta: { requiresAuth: true },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to, from, next) => {
  if (to.meta.requiresAuth) {
    const token = localStorage.getItem('access_token')
    if (!token) return next({ path: '/login', query: { next: to.path } })
  }
  next()
})

export default router
