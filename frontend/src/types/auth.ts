export type Role = 'super_admin' | 'region_admin' | 'coach' | 'lab_operator' | 'ministry'

export interface NamedRef {
  id: number
  name: string
}

export interface User {
  id: number
  username: string
  full_name: string
  role: Role
  phone: string | null
  email: string | null
  is_active: boolean
  region: NamedRef | null
  organization: NamedRef | null
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
