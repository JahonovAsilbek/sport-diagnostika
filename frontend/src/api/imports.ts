import type { Gender } from '@/types/catalog'
import type { ImportBatch } from '@/types/measurement'

import { api } from './client'

/** The .xlsx template for a group (columns = its 5 battery exercises). Returns a Blob. */
export const downloadTemplate = (ageCategory: number, gender: Gender) =>
  api
    .get('/imports/template/', {
      params: { age_category: ageCategory, gender },
      responseType: 'blob',
    })
    .then((r) => r.data as Blob)

export function uploadImport(file: File, ageCategory: number, gender: Gender, date: string) {
  const form = new FormData()
  form.append('file', file)
  form.append('age_category', String(ageCategory))
  form.append('gender', gender)
  form.append('date', date)
  return api.post<ImportBatch>('/imports/', form).then((r) => r.data)
}

export const getImport = (id: number) =>
  api.get<ImportBatch>(`/imports/${id}/`).then((r) => r.data)

export const commitImport = (id: number) =>
  api.post<ImportBatch>(`/imports/${id}/commit/`).then((r) => r.data)
