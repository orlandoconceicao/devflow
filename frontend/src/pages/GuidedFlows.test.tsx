import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it, vi } from 'vitest';
import { Dashboard } from './Dashboard';
import { ProjectsPage } from './Projects';

vi.mock('../features/auth/AuthContext', () => ({
  useAuth: () => ({ user: { first_name: 'Ana' } }),
}));
vi.mock('../features/work/hooks', () => ({
  useDashboard: () => ({ isLoading: false, data: {
    active_projects: 0, pending_tasks: 0, hours_this_month: 0, monthly_revenue: '0.00',
    recent_projects: [], upcoming_deadlines: [], recent_activity: [],
    profile_complete: false, has_clients: false, has_projects: false,
  }}),
  useProjects: () => ({ isLoading: false, isError: false, data: { count: 0, next: null, previous: null, results: [] } }),
  useClients: () => ({ isLoading: false, data: { count: 0, next: null, previous: null, results: [] } }),
  useCreateProject: () => ({ mutateAsync: vi.fn() }),
  useProject: vi.fn(),
  useProjectMembers: vi.fn(),
  useAddProjectMember: vi.fn(),
  useRemoveProjectMember: vi.fn(),
}));

describe('fluxos guiados', () => {
  it('Primeiros Passos aponta para as rotas reais', () => {
    render(<MemoryRouter><Dashboard /></MemoryRouter>);
    expect(screen.getByRole('link', { name: /Personalize seu perfil/ })).toHaveAttribute('href', '/settings/profile');
    expect(screen.getByRole('link', { name: /Cadastre seus clientes/ })).toHaveAttribute('href', '/clients?new=1');
    expect(screen.getByRole('link', { name: /Crie seu primeiro projeto/ })).toHaveAttribute('href', '/projects?new=1');
  });

  it('orienta cadastrar cliente antes de criar projeto e preserva o retorno', async () => {
    render(<MemoryRouter initialEntries={['/projects?new=1']}><ProjectsPage /></MemoryRouter>);
    expect(await screen.findByText('Nenhum cliente cadastrado')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Cadastrar cliente' })).toHaveAttribute(
      'href', '/clients?new=1&returnTo=%2Fprojects%3Fnew%3D1',
    );
  });
});
