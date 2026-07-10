import type { User } from '@/types/auth'
import type { Paginated } from '@/types/catalog'

import { api } from './client'

// Coaches the actor may assign — the /users list is scoped server-side (a region_admin sees
// only their region's coaches, a coach sees themselves).
export const getCoaches = () =>
  api
    .get<Paginated<User>>('/users/', {
      params: { role: 'coach', is_active: true, page_size: 100 },
    })
    .then((r) => r.data.results)
