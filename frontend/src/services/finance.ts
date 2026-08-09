import { api } from './api';
import type { FinanceDashboard, Invoice, PaginatedResponse, ReportData, TimeEntry } from '../types';
export const timeService = {
  list: () => api.get<PaginatedResponse<TimeEntry>>('/time-entries/').then((r) => r.data),
  active: () => api.get<TimeEntry | null>('/time-entries/active/').then((r) => r.data),
  start: (data: { project: number; description: string; billable: boolean }) =>
    api.post<TimeEntry>('/time-entries/start/', data).then((r) => r.data),
  stop: (id: number) => api.post<TimeEntry>(`/time-entries/${id}/stop/`).then((r) => r.data),
  create: (data: Partial<TimeEntry>) =>
    api.post<TimeEntry>('/time-entries/', data).then((r) => r.data),
  remove: (id: number) => api.delete(`/time-entries/${id}/`),
};
export const financeService = {
  dashboard: () => api.get<FinanceDashboard>('/finance/dashboard/').then((r) => r.data),
  expenses: () => api.get<PaginatedResponse<any>>('/expenses/').then((r) => r.data),
  revenues: () => api.get<PaginatedResponse<any>>('/revenues/').then((r) => r.data),
  invoices: () => api.get<PaginatedResponse<Invoice>>('/invoices/').then((r) => r.data),
  createExpense: (data: any) => api.post('/expenses/', data),
  createRevenue: (data: any) => api.post('/revenues/', data),
};
export const reportService = {
  get: (group: string) =>
    api.get<ReportData>('/reports/', { params: { group } }).then((r) => r.data),
  exportUrl: () => `${api.defaults.baseURL}/reports/hours/export/`,
};
