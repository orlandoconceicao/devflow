import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import { ToastProvider } from '../components/Toast';
import { organizationService } from '../services/work';
import { TeamPage } from './Team';

vi.mock('../services/work', () => ({
  organizationService: {
    ensure: vi.fn(),
    members: vi.fn(),
    invitations: vi.fn(),
    invite: vi.fn(),
    updateMember: vi.fn(),
    removeMember: vi.fn(),
    cancelInvitation: vi.fn(),
    approveMember: vi.fn(),
  },
}));

const service = vi.mocked(organizationService);
const owner = {
  id: 1,
  user: {
    id: 1,
    email: 'owner@acme.test',
    first_name: 'Ana',
    last_name: 'Owner',
    avatar: null,
    bio: '',
    language: 'pt-BR' as const,
    timezone: 'America/Cuiaba',
    theme: 'system' as const,
    pending_workspace_approval: false,
  },
  role: 'OWNER' as const,
  is_active: true,
  approval_status: 'APPROVED' as const,
  joined_at: '2026-01-01',
};
const member = {
  ...owner,
  id: 2,
  user: { ...owner.user, id: 2, email: 'member@acme.test', first_name: 'Bia', last_name: 'Silva' },
  role: 'MEMBER' as const,
};

function renderPage() {
  return render(
    <MemoryRouter>
      <ToastProvider>
        <TeamPage />
      </ToastProvider>
    </MemoryRouter>,
  );
}

describe('Equipe', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    service.ensure.mockResolvedValue({
      id: 1,
      name: 'Acme',
      slug: 'acme',
      owner: 1,
      role: 'OWNER',
    });
    service.members.mockResolvedValue({
      count: 2,
      next: null,
      previous: null,
      results: [owner, member],
    });
    service.invitations.mockResolvedValue([]);
  });

  it('Primário visualiza membros e o acesso responsivo ao chat', async () => {
    const user = userEvent.setup();
    renderPage();

    const chatLink = await screen.findByRole('link', { name: /Chat da equipe/ });
    expect(chatLink).toHaveAttribute('href', '/team/chat');
    await user.click(screen.getByRole('button', { name: /Convidar membro/ }));
    expect(screen.getByRole('heading', { name: 'Convidar membro' })).toBeInTheDocument();
    expect(screen.getByText('owner@acme.test')).toBeInTheDocument();
    expect(
      screen.queryByRole('button', { name: /Remover owner@acme.test/ }),
    ).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Remover member@acme.test/ })).toBeInTheDocument();
  });

  it('remove um Secundário após confirmação, bloqueia repetição e atualiza a lista', async () => {
    const user = userEvent.setup();
    let resolveRemoval: (() => void) | undefined;
    service.removeMember.mockReturnValue(
      new Promise((resolve) => {
        resolveRemoval = () => resolve({} as never);
      }),
    );
    vi.spyOn(window, 'confirm').mockReturnValue(true);
    renderPage();

    const remove = await screen.findByRole('button', { name: /Remover member@acme.test/ });
    await user.click(remove);

    expect(window.confirm).toHaveBeenCalledWith(
      expect.stringContaining('Bia Silva (member@acme.test)'),
    );
    expect(remove).toBeDisabled();
    expect(service.removeMember).toHaveBeenCalledTimes(1);
    resolveRemoval?.();
    await waitFor(() => expect(screen.queryByText('member@acme.test')).not.toBeInTheDocument());
    expect(await screen.findByText(/foi removido da equipe/)).toBeInTheDocument();
  });

  it('cancela convite pendente e atualiza a seção sem recarregar', async () => {
    const user = userEvent.setup();
    service.invitations.mockResolvedValue([
      {
        id: 9,
        email: 'invite@acme.test',
        role: 'ADMIN',
        expires_at: '2026-09-07T12:00:00Z',
        status: 'PENDING',
      },
    ]);
    service.cancelInvitation.mockResolvedValue({} as never);
    renderPage();

    await user.click(await screen.findByRole('button', { name: 'Cancelar convite' }));

    expect(screen.getByRole('dialog', { name: 'Cancelar convite' })).toHaveTextContent(
      'invite@acme.test',
    );
    await user.click(screen.getByRole('button', { name: 'Sim, cancelar convite' }));
    expect(service.cancelInvitation).toHaveBeenCalledWith(1, 9);
    await waitFor(() => expect(screen.queryByText('invite@acme.test')).not.toBeInTheDocument());
    expect(await screen.findByText(/Convite para invite@acme.test cancelado/)).toBeInTheDocument();
  });

  it('bloqueia o cancelamento durante a requisição e recupera a ação após erro', async () => {
    const user = userEvent.setup();
    service.invitations.mockResolvedValue([
      {
        id: 10,
        email: 'pending@acme.test',
        role: 'MEMBER',
        expires_at: '2026-09-07T12:00:00Z',
        status: 'PENDING',
      },
    ]);
    let rejectCancellation: ((reason?: unknown) => void) | undefined;
    service.cancelInvitation.mockReturnValue(
      new Promise((_, reject) => {
        rejectCancellation = reject;
      }),
    );
    renderPage();

    const cancel = await screen.findByRole('button', { name: 'Cancelar convite' });
    await user.click(cancel);
    const confirmCancellation = screen.getByRole('button', { name: 'Sim, cancelar convite' });
    await user.click(confirmCancellation);

    expect(confirmCancellation).toBeDisabled();
    expect(confirmCancellation).toHaveTextContent('Cancelando…');
    rejectCancellation?.(new Error('offline'));
    expect(await screen.findAllByText('Não foi possível cancelar o convite.')).toHaveLength(2);
    expect(screen.getAllByText('pending@acme.test').length).toBeGreaterThan(0);
    expect(screen.getByRole('button', { name: 'Sim, cancelar convite' })).toBeEnabled();
  });

  it('mantém a página estável e mostra feedback quando a remoção falha', async () => {
    const user = userEvent.setup();
    service.removeMember.mockRejectedValue(new Error('offline'));
    vi.spyOn(window, 'confirm').mockReturnValue(true);
    renderPage();

    await user.click(await screen.findByRole('button', { name: /Remover member@acme.test/ }));

    expect(await screen.findAllByText('Não foi possível remover o membro.')).toHaveLength(2);
    expect(screen.getByText('member@acme.test')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Remover member@acme.test/ })).toBeEnabled();
  });

  it('Secundário não visualiza a gestão da equipe', async () => {
    service.ensure.mockResolvedValue({
      id: 1,
      name: 'Acme',
      slug: 'acme',
      owner: 1,
      role: 'MEMBER',
    });
    renderPage();

    expect(await screen.findByText('Acesso restrito')).toBeInTheDocument();
    await waitFor(() => expect(service.members).not.toHaveBeenCalled());
    expect(screen.queryByRole('button', { name: /Remover da equipe/ })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /Cancelar convite/ })).not.toBeInTheDocument();
  });
});
