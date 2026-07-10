import { createRouter, createWebHistory } from 'vue-router'

import AppLayout from '@/layouts/AppLayout.vue'
import { useAuthStore } from '@/stores/auth'
import type { Role } from '@/types/auth'
import { DATA_ENTRY_ROLES } from '@/utils/permissions'

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
        {
          path: 'athletes',
          name: 'athletes',
          component: () => import('@/views/athletes/AthletesView.vue'),
        },
        {
          path: 'athletes/new',
          name: 'athlete-new',
          component: () => import('@/views/athletes/AthleteFormView.vue'),
          meta: { title: 'Yangi sportchi', roles: DATA_ENTRY_ROLES },
        },
        {
          path: 'athletes/:id',
          name: 'athlete-card',
          component: () => import('@/views/athletes/AthleteCardView.vue'),
        },
        {
          path: 'athletes/:id/edit',
          name: 'athlete-edit',
          component: () => import('@/views/athletes/AthleteFormView.vue'),
          meta: { title: 'Sportchini tahrirlash', roles: DATA_ENTRY_ROLES },
        },
        {
          path: 'measurements',
          name: 'measurements',
          component: () => import('@/views/measurements/MeasurementsView.vue'),
        },
        {
          path: 'measurements/import',
          name: 'measurements-import',
          component: () => import('@/views/measurements/ImportView.vue'),
          meta: { title: 'Excel import', roles: DATA_ENTRY_ROLES },
        },
        {
          path: 'measurements/session/:id',
          name: 'session',
          component: () => import('@/views/measurements/SessionView.vue'),
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
        {
          path: 'catalog',
          name: 'catalog',
          component: () => import('@/views/catalog/CatalogView.vue'),
        },
        {
          path: 'catalog/norms',
          name: 'catalog-norms',
          component: () => import('@/views/catalog/NormsView.vue'),
          meta: { title: 'Normalar', roles: ['super_admin'] },
        },
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
