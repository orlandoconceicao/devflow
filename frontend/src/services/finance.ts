import { api } from './api';
import type {
  Expense,
  FinanceDashboard,
  Invoice,
  PaginatedResponse,
  ReportData,
  Revenue,
  TimeEntry,
} from '../types';
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
  expenses: () => api.get<PaginatedResponse<Expense>>('/expenses/').then((r) => r.data),
  revenues: () => api.get<PaginatedResponse<Revenue>>('/revenues/').then((r) => r.data),
  invoices: () => api.get<PaginatedResponse<Invoice>>('/invoices/').then((r) => r.data),
  createExpense: (data: Partial<Expense>) => api.post<Expense>('/expenses/', data),
  createRevenue: (data: Partial<Revenue>) => api.post<Revenue>('/revenues/', data),
};
export const reportService = {
  get: (group: string) =>
    api.get<ReportData>('/reports/', { params: { group } }).then((r) => r.data),
  exportUrl: () => `${api.defaults.baseURL}/reports/hours/export/`,
};
