import type { Role } from '@/types/auth'

// Mirrors the backend DATA_ENTRY_ROLES — the roles allowed to write scoped data (athletes,
// measurements, …). ministry is read-only oversight. The server enforces this; the UI uses it
// only to hide write actions (never as the sole gate).
export const DATA_ENTRY_ROLES: Role[] = ['super_admin', 'region_admin', 'coach', 'lab_operator']

export function canWrite(role: Role | null): boolean {
  return role !== null && DATA_ENTRY_ROLES.includes(role)
}
