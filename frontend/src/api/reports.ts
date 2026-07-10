import type { Paginated } from '@/types/catalog'

import { api } from './client'

export type ReportType = 'athlete' | 'region' | 'sport' | 'republic'
export type ReportFormat = 'pdf' | 'word' | 'excel'
export type ReportStatus = 'pending' | 'processing' | 'done' | 'failed'

export const REPORT_TYPE_LABELS: Record<ReportType, string> = {
  athlete: 'Sportchi',
  region: 'Viloyat',
  sport: 'Sport turi',
  republic: 'Respublika',
}
export const REPORT_FORMAT_LABELS: Record<ReportFormat, string> = {
  pdf: 'PDF',
  word: 'Word',
  excel: 'Excel',
}
export const REPORT_STATUS_LABELS: Record<ReportStatus, string> = {
  pending: 'Navbatda',
  processing: 'Ishlanmoqda',
  done: 'Tayyor',
  failed: 'Xato',
}
export const REPORT_STATUS_SEVERITY: Record<ReportStatus, string> = {
  pending: 'secondary',
  processing: 'info',
  done: 'success',
  failed: 'danger',
}

export interface Report {
  id: number
  type: ReportType
  format: ReportFormat
  params: Record<string, number | string | undefined>
  status: ReportStatus
  error: string
  created_at: string
  completed_at: string | null
}

export interface ReportRequest {
  type: ReportType
  format: ReportFormat
  params: Record<string, number | string>
}

// A report is visible only to its requester (super_admin/ministry see all) — enforced server-side.
export const listReports = () =>
  api.get<Paginated<Report>>('/reports/').then((r) => r.data)

export const getReport = (id: number) => api.get<Report>(`/reports/${id}/`).then((r) => r.data)

// 202 Accepted — the worker builds it async; poll status then download when `done`.
export const createReport = (payload: ReportRequest) =>
  api.post<Report>('/reports/', payload).then((r) => r.data)

// The generated file (blob) once `done` — the backend 409s otherwise. Filename comes from the
// Content-Disposition header the FileResponse sets.
export async function downloadReport(id: number): Promise<{ blob: Blob; filename: string }> {
  const res = await api.get<Blob>(`/reports/${id}/download/`, { responseType: 'blob' })
  const disposition = String(res.headers['content-disposition'] ?? '')
  const match = /filename="?([^"]+)"?/.exec(disposition)
  return { blob: res.data, filename: match ? match[1] : `report-${id}` }
}
