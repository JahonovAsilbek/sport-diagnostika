import type { Role } from '@/types/auth'

export interface NavItem {
  label: string
  icon: string // primeicons class
  to: string // route path
  roles?: Role[] // visible only to these roles; undefined = every authenticated role
}

// The sidebar menu. Data is scoped server-side regardless, so this is UX, not access control —
// route guards (FRNTND-6) + the backend enforce the real rules. Sections point at routes that
// arrive in later F-blocks (placeholder until then).
export const NAV_ITEMS: NavItem[] = [
  { label: 'Bosh sahifa', icon: 'pi pi-home', to: '/' },
  { label: 'Sportchilar', icon: 'pi pi-users', to: '/athletes' },
  { label: 'Oʻlchovlar', icon: 'pi pi-pencil', to: '/measurements' },
  { label: 'Reyting', icon: 'pi pi-chart-bar', to: '/rating' },
  { label: 'Taqqoslash', icon: 'pi pi-arrow-right-arrow-left', to: '/comparison' },
  { label: 'Tavsiyalar', icon: 'pi pi-lightbulb', to: '/recommendations' },
  { label: 'Hisobotlar', icon: 'pi pi-file', to: '/reports' },
  { label: 'Katalog', icon: 'pi pi-book', to: '/catalog' },
  {
    label: 'Foydalanuvchilar',
    icon: 'pi pi-id-card',
    to: '/users',
    roles: ['super_admin', 'region_admin'],
  },
]

export function visibleNav(role: Role | null): NavItem[] {
  return NAV_ITEMS.filter((item) => !item.roles || (role !== null && item.roles.includes(role)))
}
