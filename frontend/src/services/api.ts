import axios, { type AxiosError, type InternalAxiosRequestConfig } from 'axios';
const API_URL = import.meta.env.VITE_API_URL ?? '/api';
export const api = axios.create({ baseURL: API_URL });

export function clearAuthStorage() {
  localStorage.removeItem('access');
  localStorage.removeItem('refresh');
  localStorage.removeItem('organization_id');
}

export interface ApiErrorDetails {
  message: string;
  fields: Record<string, string>;
}

const errorText = (value: unknown): string => {
  if (typeof value === 'string') return value;
  if (Array.isArray(value)) return value.map(errorText).filter(Boolean).join(' ');
  if (value && typeof value === 'object') {
    return Object.values(value).map(errorText).filter(Boolean).join(' ');
  }
  return '';
};

export function getApiErrorDetails(error: unknown, fallback: string): ApiErrorDetails {
  if (!axios.isAxiosError(error)) return { message: fallback, fields: {} };

  const responseData = error.response?.data;
  const payload =
    responseData && typeof responseData === 'object' && 'error' in responseData
      ? (responseData as { error?: { details?: unknown } }).error?.details
      : responseData;
  const fields: Record<string, string> = {};

  if (payload && typeof payload === 'object' && !Array.isArray(payload)) {
    Object.entries(payload).forEach(([field, value]) => {
      const message = errorText(value);
      if (message) fields[field] = message;
    });
  }

  return {
    message: fields.non_field_errors ?? fields.detail ?? (errorText(payload) || fallback),
    fields,
  };
}

let refreshing: Promise<string> | null = null;
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access');
  const organization = localStorage.getItem('organization_id');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  if (organization) config.headers['X-Organization-ID'] = organization;
  return config;
});
api.interceptors.response.use(
  (r) => r,
  async (error: AxiosError) => {
    const original = error.config as
      (InternalAxiosRequestConfig & { _retry?: boolean }) | undefined;
    if (
      error.response?.status !== 401 ||
      !original ||
      original._retry ||
      original.url?.includes('/auth/refresh/')
    )
      throw error;
    original._retry = true;
    const refresh = localStorage.getItem('refresh');
    if (!refresh) {
      clearAuthStorage();
      throw error;
    }
    refreshing ??= axios
      .post<{ access: string; refresh?: string }>(`${API_URL}/auth/refresh/`, { refresh })
      .then(({ data }) => {
        localStorage.setItem('access', data.access);
        if (data.refresh) localStorage.setItem('refresh', data.refresh);
        return data.access;
      })
      .finally(() => {
        refreshing = null;
      });
    try {
      original.headers.Authorization = `Bearer ${await refreshing}`;
      return api(original);
    } catch (e) {
      clearAuthStorage();
      if (window.location.pathname !== '/login') window.location.assign('/login');
      throw e;
    }
  },
);
