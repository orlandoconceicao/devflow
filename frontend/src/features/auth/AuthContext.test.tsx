import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import type { User } from '../../types';

const apiMocks = vi.hoisted(() => ({
  get: vi.fn(),
  post: vi.fn(),
  clearAuthStorage: vi.fn(() => {
    localStorage.removeItem('access');
    localStorage.removeItem('refresh');
    localStorage.removeItem('organization_id');
  }),
}));

vi.mock('../../services/api', () => ({
  api: { get: apiMocks.get, post: apiMocks.post },
  clearAuthStorage: apiMocks.clearAuthStorage,
}));

import { AuthProvider, useAuth } from './AuthContext';

const user: User = {
  id: 7,
  email: 'dev@devflow.test',
  first_name: 'Dev',
  last_name: 'Flow',
  avatar: null,
  bio: '',
  language: 'pt-BR',
  timezone: 'America/Cuiaba',
  theme: 'system',
  pending_workspace_approval: false,
};

function Probe() {
  const auth = useAuth();
  return (
    <>
      <span>{auth.isLoading ? 'loading' : (auth.user?.email ?? 'anonymous')}</span>
      <button onClick={() => void auth.login('  DEV@DEVFLOW.TEST ', 'secret')}>login</button>
      <button onClick={() => void auth.logout()}>logout</button>
    </>
  );
}

describe('AuthProvider', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
  });

  it('starts anonymously without making a profile request when no token exists', async () => {
    render(
      <AuthProvider>
        <Probe />
      </AuthProvider>,
    );

    expect(await screen.findByText('anonymous')).toBeInTheDocument();
    expect(apiMocks.get).not.toHaveBeenCalled();
  });

  it('normalizes credentials and persists the tokens returned by login', async () => {
    apiMocks.post.mockResolvedValueOnce({
      data: { access: 'access-token', refresh: 'refresh-token', user },
    });
    render(
      <AuthProvider>
        <Probe />
      </AuthProvider>,
    );

    await userEvent.click(await screen.findByRole('button', { name: 'login' }));

    await waitFor(() => expect(screen.getByText(user.email)).toBeInTheDocument());
    expect(apiMocks.post).toHaveBeenCalledWith('/auth/login/', {
      email: 'dev@devflow.test',
      password: 'secret',
    });
    expect(localStorage.getItem('access')).toBe('access-token');
    expect(localStorage.getItem('refresh')).toBe('refresh-token');
  });

  it('restores a saved session and clears invalid credentials', async () => {
    localStorage.setItem('refresh', 'expired');
    localStorage.setItem('organization_id', '12');
    apiMocks.get.mockRejectedValueOnce(new Error('unauthorized'));

    render(
      <AuthProvider>
        <Probe />
      </AuthProvider>,
    );

    expect(await screen.findByText('anonymous')).toBeInTheDocument();
    expect(apiMocks.get).toHaveBeenCalledWith('/auth/me/');
    expect(apiMocks.clearAuthStorage).toHaveBeenCalled();
    expect(localStorage.getItem('organization_id')).toBeNull();
  });

  it('clears the local session even when remote logout fails', async () => {
    localStorage.setItem('refresh', 'refresh-token');
    apiMocks.get.mockResolvedValueOnce({ data: user });
    apiMocks.post.mockRejectedValueOnce(new Error('offline'));
    render(
      <AuthProvider>
        <Probe />
      </AuthProvider>,
    );
    await screen.findByText(user.email);

    await userEvent.click(screen.getByRole('button', { name: 'logout' }));

    await waitFor(() => expect(screen.getByText('anonymous')).toBeInTheDocument());
    expect(apiMocks.post).toHaveBeenCalledWith('/auth/logout/', { refresh: 'refresh-token' });
    expect(localStorage.getItem('refresh')).toBeNull();
  });

  it('removes every local credential before remote logout finishes', async () => {
    let finishLogout!: () => void;
    localStorage.setItem('refresh', 'refresh-token');
    localStorage.setItem('organization_id', '42');
    apiMocks.get.mockResolvedValueOnce({ data: user });
    apiMocks.post.mockReturnValueOnce(
      new Promise<void>((resolve) => {
        finishLogout = resolve;
      }),
    );
    render(
      <AuthProvider>
        <Probe />
      </AuthProvider>,
    );
    await screen.findByText(user.email);

    await userEvent.click(screen.getByRole('button', { name: 'logout' }));
    expect(localStorage.getItem('access')).toBeNull();
    expect(localStorage.getItem('refresh')).toBeNull();
    expect(localStorage.getItem('organization_id')).toBeNull();
    expect(screen.getByText('anonymous')).toBeInTheDocument();
    finishLogout();
  });
});
