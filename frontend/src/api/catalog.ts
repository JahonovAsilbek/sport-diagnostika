import type {
  AgeCategory,
  DarajaThreshold,
  District,
  Exercise,
  Gender,
  Norm,
  NormWrite,
  Organization,
  OrganizationWrite,
  OrgType,
  Paginated,
  Region,
  SportType,
  TestBattery,
} from '@/types/catalog'

import { api } from './client'

// Reference lists are small — fetch a single large page (max_page_size=100).
async function listAll<T>(url: string, params?: Record<string, unknown>): Promise<T[]> {
  const { data } = await api.get<Paginated<T>>(url, { params: { page_size: 100, ...params } })
  return data.results
}

export const getRegions = () => listAll<Region>('/catalog/regions/')
export const getDistricts = (region: number) =>
  listAll<District>('/catalog/districts/', { region })
export const getSportTypes = () => listAll<SportType>('/catalog/sport-types/')
export const getAgeCategories = () => listAll<AgeCategory>('/catalog/age-categories/')
export const getExercises = () => listAll<Exercise>('/catalog/exercises/')
export const getOrganizations = (params?: { region?: number; type?: OrgType }) =>
  listAll<Organization>('/catalog/organizations/', params)

// Organization management (FRNTND-28) — write is super_admin-only (ReadOnlyOrSuperAdmin, BCKND-21).
export const createOrganization = (payload: OrganizationWrite) =>
  api.post<Organization>('/catalog/organizations/', payload).then((r) => r.data)
export const updateOrganization = (id: number, payload: OrganizationWrite) =>
  api.put<Organization>(`/catalog/organizations/${id}/`, payload).then((r) => r.data)
export const deleteOrganization = (id: number) => api.delete(`/catalog/organizations/${id}/`)
export const getBatteries = (params?: { age_category?: number; gender?: Gender }) =>
  listAll<TestBattery>('/catalog/batteries/', params)
export const getDarajaThresholds = () => listAll<DarajaThreshold>('/catalog/daraja-thresholds/')

// DRF serializes DecimalField to strings — coerce band bounds to numbers for the editor/checks.
function coerceNorm(n: Norm): Norm {
  return {
    ...n,
    bands: n.bands.map((b) => ({
      points: Number(b.points),
      lower_bound: b.lower_bound === null ? null : Number(b.lower_bound),
      upper_bound: b.upper_bound === null ? null : Number(b.upper_bound),
    })),
  }
}

export async function getNorms(params?: { exercise?: number; gender?: Gender; page?: number }) {
  const { data } = await api.get<Paginated<Norm>>('/catalog/norms/', {
    params: { page_size: 100, ...params },
  })
  return { ...data, results: data.results.map(coerceNorm) }
}

export const createNorm = (payload: NormWrite) =>
  api.post<Norm>('/catalog/norms/', payload).then((r) => coerceNorm(r.data))
export const updateNorm = (id: number, payload: NormWrite) =>
  api.put<Norm>(`/catalog/norms/${id}/`, payload).then((r) => coerceNorm(r.data))
export const deleteNorm = (id: number) => api.delete(`/catalog/norms/${id}/`)
