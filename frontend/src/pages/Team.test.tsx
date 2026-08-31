import { render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { organizationService } from '../services/work';
import { TeamPage } from './Team';
import { MemoryRouter } from 'react-router-dom';

vi.mock('../services/work', () => ({ organizationService: { ensure:vi.fn(), members:vi.fn(), invitations:vi.fn(), invite:vi.fn(), updateMember:vi.fn(), removeMember:vi.fn(), approveMember:vi.fn() } }));
const service = vi.mocked(organizationService);

describe('Equipe', () => {
  beforeEach(() => vi.clearAllMocks());
  it('Owner visualiza lista e botão de convite', async () => {
    service.ensure.mockResolvedValue({id:1,name:'Acme',slug:'acme',owner:1,role:'OWNER'});
    service.members.mockResolvedValue({count:1,next:null,previous:null,results:[{id:1,user:{id:1,email:'owner@acme.test',first_name:'Ana',last_name:'Owner',avatar:null,bio:'',language:'pt-BR',timezone:'America/Cuiaba',theme:'system',pending_workspace_approval:false},role:'OWNER',is_active:true,approval_status:'APPROVED',joined_at:'2026-01-01'}]});
    service.invitations.mockResolvedValue([]);
    render(<MemoryRouter><TeamPage/></MemoryRouter>);
    const chatLink = await screen.findByRole('link',{name:/Chat da equipe/});
    expect(chatLink).toHaveAttribute('href', '/team/chat');
    expect(screen.queryByRole('button',{name:/Convidar membro/})).not.toBeInTheDocument();
    expect(screen.getByText('owner@acme.test')).toBeInTheDocument();
  });
  it('Member não visualiza gestão da equipe', async () => {
    service.ensure.mockResolvedValue({id:1,name:'Acme',slug:'acme',owner:1,role:'MEMBER'});
    render(<MemoryRouter><TeamPage/></MemoryRouter>);
    expect(await screen.findByText('Acesso restrito')).toBeInTheDocument();
    await waitFor(()=>expect(service.members).not.toHaveBeenCalled());
    expect(screen.queryByRole('button',{name:/Convidar membro/})).not.toBeInTheDocument();
  });
});
