import type { Role } from '@/types/auth'

export interface NavItem {
  labelKey: string // i18n key under the `nav` namespace, resolved at render
  icon: string // primeicons class
  to: string // route path
  roles?: Role[] // visible only to these roles; undefined = every authenticated role
}

// The sidebar menu. Data is scoped server-side regardless, so this is UX, not access control —
// route guards (FRNTND-6) + the backend enforce the real rules. Labels are i18n keys (FRNTND-25),
// resolved in the shell.
export const NAV_ITEMS: NavItem[] = [
  { labelKey: 'nav.home', icon: 'pi pi-home', to: '/' },
  { labelKey: 'nav.athletes', icon: 'pi pi-users', to: '/athletes' },
  { labelKey: 'nav.measurements', icon: 'pi pi-pencil', to: '/measurements' },
  { labelKey: 'nav.rating', icon: 'pi pi-chart-bar', to: '/rating' },
  { labelKey: 'nav.comparison', icon: 'pi pi-arrow-right-arrow-left', to: '/comparison' },
  { labelKey: 'nav.recommendations', icon: 'pi pi-lightbulb', to: '/recommendations' },
  { labelKey: 'nav.reports', icon: 'pi pi-file', to: '/reports' },
  { labelKey: 'nav.catalog', icon: 'pi pi-book', to: '/catalog' },
  {
    labelKey: 'nav.users',
    icon: 'pi pi-id-card',
    to: '/users',
    roles: ['super_admin', 'region_admin'],
  },
]

export function visibleNav(role: Role | null): NavItem[] {
  return NAV_ITEMS.filter((item) => !item.roles || (role !== null && item.roles.includes(role)))
}
