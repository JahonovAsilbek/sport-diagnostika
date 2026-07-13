export type Role = 'super_admin' | 'region_admin' | 'coach' | 'lab_operator' | 'ministry'

export interface NamedRef {
  id: number
  name: string
}

export interface User {
  id: number
  username: string
  full_name: string
  first_name: string
  last_name: string
  role: Role
  phone: string | null
  email: string | null
  is_active: boolean
  region: NamedRef | null
  organization: NamedRef | null
}

/** Create/update payload — region/organization are PKs (the read `User` nests them), and
 * `password` is write-only (required on create, omit on edit to keep the current one). */
export interface UserWrite {
  username: string
  password?: string
  first_name?: string
  last_name?: string
  email?: string
  phone?: string
  role: Role | null
  is_active?: boolean
  region: number | null
  organization: number | null
}

/** POST /auth/login/ — the backend returns the tokens plus the profile in one call. */
export interface LoginResponse {
  access: string
  refresh: string
  user: User
}

export interface TokenPair {
  access: string
  refresh: string
}
