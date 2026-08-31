import axios, { AxiosError, type AxiosResponse, type InternalAxiosRequestConfig } from 'axios';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { api, clearAuthStorage, getApiErrorDetails, organizationIdForRequest } from './api';

describe('organization request context', () => {
  beforeEach(() => localStorage.clear());

  it('adds a valid organization only to workspace endpoints', () => {
    localStorage.setItem('organization_id', '42');
    expect(organizationIdForRequest('/dashboard/')).toBe('42');
    expect(organizationIdForRequest('/projects/')).toBe('42');
  });

  it.each(['/auth/login/', '/auth/register/', '/auth/refresh/', '/organizations/'])(
    'does not attach an organization to %s',
    (url) => {
      localStorage.setItem('organization_id', '42');
      expect(organizationIdForRequest(url)).toBeNull();
    },
  );

  it.each(['', 'null', 'undefined', 'invalid', '-1'])(
    'rejects invalid organization value %s',
    (value) => {
      localStorage.setItem('organization_id', value);
      expect(organizationIdForRequest('/dashboard/')).toBeNull();
    },
  );
});

describe('API client behavior', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.restoreAllMocks();
  });

  it('attaches authentication and organization only to workspace requests', async () => {
    localStorage.setItem('access', 'access-token');
    localStorage.setItem('organization_id', '42');
    const configs: InternalAxiosRequestConfig[] = [];
    const adapter = async (config: InternalAxiosRequestConfig): Promise<AxiosResponse> => {
      configs.push(config);
      return { data: {}, status: 200, statusText: 'OK', headers: {}, config };
    };

    await api.get('/projects/', { adapter });
    await api.get('/auth/me/', { adapter });

    expect(configs[0].headers.Authorization).toBe('Bearer access-token');
    expect(configs[0].headers['X-Organization-ID']).toBe('42');
    expect(configs[1].headers.Authorization).toBe('Bearer access-token');
    expect(configs[1].headers['X-Organization-ID']).toBeUndefined();
  });

  it('refreshes once after a 401 and retries with the new access token', async () => {
    localStorage.setItem('refresh', 'old-refresh');
    vi.spyOn(axios, 'post').mockResolvedValueOnce({
      data: { access: 'new-access', refresh: 'new-refresh' },
    });
    let attempts = 0;
    const adapter = async (config: InternalAxiosRequestConfig): Promise<AxiosResponse> => {
      attempts += 1;
      if (attempts === 1) {
        throw new AxiosError('unauthorized', '401', config, undefined, {
          data: {}, status: 401, statusText: 'Unauthorized', headers: {}, config,
        });
      }
      return { data: { ok: true }, status: 200, statusText: 'OK', headers: {}, config };
    };

    const response = await api.get('/projects/', { adapter });

    expect(response.data).toEqual({ ok: true });
    expect(attempts).toBe(2);
    expect(axios.post).toHaveBeenCalledWith('/api/auth/refresh/', { refresh: 'old-refresh' });
    expect(localStorage.getItem('access')).toBe('new-access');
    expect(localStorage.getItem('refresh')).toBe('new-refresh');
  });

  it('normalizes nested validation errors and clears all session keys', () => {
    const error = new AxiosError('bad request', '400', undefined, undefined, {
      data: { email: ['E-mail inválido.'], detail: 'Revise os campos.' },
      status: 400,
      statusText: 'Bad Request',
      headers: {},
      config: {} as InternalAxiosRequestConfig,
    });

    expect(getApiErrorDetails(error, 'Falha')).toEqual({
      message: 'Revise os campos.',
      fields: { email: 'E-mail inválido.', detail: 'Revise os campos.' },
    });
    localStorage.setItem('access', 'a');
    localStorage.setItem('refresh', 'r');
    localStorage.setItem('organization_id', '1');
    clearAuthStorage();
    expect(localStorage.length).toBe(0);
  });
});
