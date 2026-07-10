import { createRouter, createWebHistory } from 'vue-router'

import AppLayout from '@/layouts/AppLayout.vue'
import { useAuthStore } from '@/stores/auth'
import type { Role } from '@/types/auth'

declare module 'vue-router' {
  interface RouteMeta {
    requiresAuth?: boolean
    roles?: Role[]
    title?: string
  }
}

// Sections whose real views arrive in later F-blocks render a placeholder for now.
const placeholder = () => import('@/views/PlaceholderView.vue')

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/login', name: 'login', component: () => import('@/views/LoginView.vue') },
    {
      // Authenticated app — everything below renders inside the shell (navbar + sidebar).
      path: '/',
      component: AppLayout,
      meta: { requiresAuth: true },
      children: [
        { path: '', name: 'home', component: () => import('@/views/HomeView.vue') },
        { path: 'athletes', name: 'athletes', component: placeholder, meta: { title: 'Sportchilar' } },
        {
          path: 'measurements',
          name: 'measurements',
          component: placeholder,
          meta: { title: 'Oʻlchovlar' },
        },
        { path: 'rating', name: 'rating', component: placeholder, meta: { title: 'Reyting' } },
        {
          path: 'comparison',
          name: 'comparison',
          component: placeholder,
          meta: { title: 'Taqqoslash' },
        },
        {
          path: 'recommendations',
          name: 'recommendations',
          component: placeholder,
          meta: { title: 'Tavsiyalar' },
        },
        { path: 'reports', name: 'reports', component: placeholder, meta: { title: 'Hisobotlar' } },
        { path: 'catalog', name: 'catalog', component: placeholder, meta: { title: 'Katalog' } },
        {
          path: 'users',
          name: 'users',
          component: placeholder,
          meta: { title: 'Foydalanuvchilar', roles: ['super_admin', 'region_admin'] },
        },
      ],
    },
    { path: '/403', name: 'forbidden', component: () => import('@/views/ForbiddenView.vue') },
    {
      path: '/:pathMatch(.*)*',
      name: 'not-found',
      component: () => import('@/views/NotFoundView.vue'),
    },
  ],
})

router.beforeEach((to) => {
  const auth = useAuthStore()
  if (to.meta.requiresAuth && !auth.isAuthenticated) {
    return { name: 'login', query: { redirect: to.fullPath } }
  }
  if (to.name === 'login' && auth.isAuthenticated) {
    return { name: 'home' }
  }
  // Role-gated routes (e.g. user management) → 403 for the wrong role.
  if (to.meta.roles && auth.role && !to.meta.roles.includes(auth.role)) {
    return { name: 'forbidden' }
  }
})

export default router
