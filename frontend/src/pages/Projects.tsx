import { zodResolver } from '@hookform/resolvers/zod';
import { Plus, Search, UserPlus, X } from 'lucide-react';
import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { useQuery } from '@tanstack/react-query';
import { Link, useParams } from 'react-router-dom';
import { z } from 'zod';
import { ProjectCard } from '../components/ProjectCard';
import { Kanban } from '../components/Kanban';
import { Button, EmptyState, ErrorState, Input, LoadingState, Select } from '../components/ui';
import {
  useAddProjectMember,
  useClients,
  useCreateProject,
  useProject,
  useProjectMembers,
  useProjects,
  useRemoveProjectMember,
} from '../features/work/hooks';
import { api } from '../services/api';
import type {
  OrganizationMembership,
  PaginatedResponse,
  ProjectPriority,
  ProjectRole,
  ProjectStatus,
} from '../types';
import { formatCurrency, formatDate } from '../utils/format';
const schema = z
  .object({
    name: z.string().min(2, 'Informe o nome'),
    client: z.number().positive('Selecione o cliente'),
    description: z.string().optional(),
    status: z.enum(['PLANNING', 'ACTIVE', 'ON_HOLD', 'COMPLETED', 'CANCELLED']),
    priority: z.enum(['LOW', 'MEDIUM', 'HIGH', 'URGENT']),
    start_date: z.string().optional(),
    due_date: z.string().optional(),
    progress: z.number().min(0).max(100),
    budget: z.string().optional(),
  })
  .refine((v) => !v.start_date || !v.due_date || v.due_date >= v.start_date, {
    path: ['due_date'],
    message: 'Prazo anterior ao início',
  });
type Form = z.infer<typeof schema>;
const statusLabel: Record<ProjectStatus, string> = {
  PLANNING: 'Planejamento',
  ACTIVE: 'Ativo',
  ON_HOLD: 'Pausado',
  COMPLETED: 'Concluído',
  CANCELLED: 'Cancelado',
};
const priorityLabel: Record<ProjectPriority, string> = {
  LOW: 'Baixa',
  MEDIUM: 'Média',
  HIGH: 'Alta',
  URGENT: 'Urgente',
};
export function ProjectsPage() {
  const [search, setSearch] = useState('');
  const [status, setStatus] = useState('');
  const [open, setOpen] = useState(false);
  const projects = useProjects({ search, status });
  const clients = useClients();
  const create = useCreateProject();
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<Form>({
    resolver: zodResolver(schema),
    defaultValues: {
      name: '',
      description: '',
      status: 'PLANNING',
      priority: 'MEDIUM',
      start_date: '',
      due_date: '',
      progress: 0,
      budget: '',
    },
  });
  return (
    <>
      <div className="page-head">
        <div>
          <h1>Projetos</h1>
          <p>Gerencie todos os projetos da sua organização.</p>
        </div>
        <Button onClick={() => setOpen(true)}>
          <Plus size={18} /> Novo projeto
        </Button>
      </div>
      <div className="toolbar">
        <div className="search-field">
          <Search size={17} />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Buscar projetos…"
          />
        </div>
        <Select value={status} onChange={(e) => setStatus(e.target.value)}>
          <option value="">Todos os status</option>
          {Object.entries(statusLabel).map(([v, l]) => (
            <option value={v} key={v}>
              {l}
            </option>
          ))}
        </Select>
      </div>
      {projects.isLoading ? (
        <LoadingState />
      ) : projects.isError ? (
        <ErrorState message="Não foi possível carregar os projetos." />
      ) : !projects.data?.results.length ? (
        <EmptyState
          title="Você ainda não possui projetos"
          description="Crie seu primeiro projeto e acompanhe o progresso pelo DevFlow."
        />
      ) : (
        <div className="project-grid">
          {projects.data.results.map((p) => (
            <ProjectCard key={p.id} project={p} />
          ))}
        </div>
      )}
      {open && (
        <div className="modal-backdrop">
          <div className="form-modal wide">
            <div>
              <h2>Novo projeto</h2>
              <button onClick={() => setOpen(false)}>×</button>
            </div>
            <form
              onSubmit={handleSubmit(async (v) => {
                await create.mutateAsync({
                  ...v,
                  budget: v.budget || null,
                  start_date: v.start_date || null,
                  due_date: v.due_date || null,
                });
                reset();
                setOpen(false);
              })}
            >
              <div className="form-row">
                <label>
                  Nome
                  <Input {...register('name')} />
                  <small>{errors.name?.message}</small>
                </label>
                <label>
                  Cliente
                  <Select {...register('client', { valueAsNumber: true })}>
                    <option value="">Selecione</option>
                    {clients.data?.results.map((c) => (
                      <option key={c.id} value={c.id}>
                        {c.name}
                      </option>
                    ))}
                  </Select>
                  <small>{errors.client?.message}</small>
                </label>
              </div>
              <label>
                Descrição
                <textarea {...register('description')} />
              </label>
              <div className="form-row">
                <label>
                  Status
                  <Select {...register('status')}>
                    {Object.entries(statusLabel).map(([v, l]) => (
                      <option value={v} key={v}>
                        {l}
                      </option>
                    ))}
                  </Select>
                </label>
                <label>
                  Prioridade
                  <Select {...register('priority')}>
                    {Object.entries(priorityLabel).map(([v, l]) => (
                      <option value={v} key={v}>
                        {l}
                      </option>
                    ))}
                  </Select>
                </label>
              </div>
              <div className="form-row">
                <label>
                  Data inicial
                  <Input type="date" {...register('start_date')} />
                </label>
                <label>
                  Prazo
                  <Input type="date" {...register('due_date')} />
                  <small>{errors.due_date?.message}</small>
                </label>
              </div>
              <div className="form-row">
                <label>
                  Progresso
                  <Input
                    type="number"
                    min="0"
                    max="100"
                    {...register('progress', { valueAsNumber: true })}
                  />
                </label>
                <label>
                  Orçamento
                  <Input type="number" min="0" step="0.01" {...register('budget')} />
                </label>
              </div>
              <footer>
                <Button type="button" className="secondary" onClick={() => setOpen(false)}>
                  Cancelar
                </Button>
                <Button disabled={isSubmitting}>Criar projeto</Button>
              </footer>
            </form>
          </div>
        </div>
      )}
    </>
  );
}
export function ProjectDetail() {
  const id = Number(useParams().id);
  const [tab, setTab] = useState('overview');
  const [memberOpen, setMemberOpen] = useState(false);
  const project = useProject(id);
  const members = useProjectMembers(id);
  const orgId = localStorage.getItem('organization_id');
  const organizationMembers = useQuery({
    queryKey: ['organization-members', orgId],
    queryFn: () =>
      api
        .get<PaginatedResponse<OrganizationMembership>>(`/organizations/${orgId}/members/`)
        .then((r) => r.data.results),
    enabled: !!orgId,
  });
  const add = useAddProjectMember(id);
  const remove = useRemoveProjectMember(id);
  const [user, setUser] = useState('');
  const [role, setRole] = useState<ProjectRole>('MEMBER');
  if (project.isLoading) return <LoadingState />;
  if (!project.data) return <ErrorState message="Projeto não encontrado." />;
  const p = project.data;
  return (
    <>
      <div className="project-detail-head">
        <div>
          <Link to="/projects">← Projetos</Link>
          <h1>{p.name}</h1>
          <p>{p.client_detail.name}</p>
        </div>
        <div>
          <span className={`status status-${p.status.toLowerCase()}`}>{statusLabel[p.status]}</span>
          <span className={`priority priority-${p.priority.toLowerCase()}`}>
            {priorityLabel[p.priority]}
          </span>
        </div>
      </div>
      <nav className="tabs">
        {[
          ['overview', 'Visão geral'],
          ['team', 'Equipe'],
          ['activity', 'Atividade'],
          ['tasks', 'Tarefas'],
          ['kanban', 'Kanban'],
          ['files', 'Arquivos'],
          ['finance', 'Financeiro'],
        ].map(([v, l]) => (
          <button className={tab === v ? 'active' : ''} onClick={() => setTab(v)} key={v}>
            {l}
          </button>
        ))}
      </nav>
      {tab === 'overview' && (
        <div className="detail-grid">
          <section className="panel">
            <h2>Sobre o projeto</h2>
            <p>{p.description || 'Nenhuma descrição cadastrada.'}</p>
            <dl>
              <dt>Cliente</dt>
              <dd>{p.client_detail.name}</dd>
              <dt>Data inicial</dt>
              <dd>{formatDate(p.start_date)}</dd>
              <dt>Prazo</dt>
              <dd>{formatDate(p.due_date)}</dd>
              <dt>Orçamento</dt>
              <dd>{p.budget ? formatCurrency(p.budget) : 'Não informado'}</dd>
              <dt>Criado por</dt>
              <dd>{p.created_by_detail.first_name || p.created_by_detail.email}</dd>
            </dl>
          </section>
          <section className="panel">
            <h2>Progresso</h2>
            <strong className="big-progress">{p.progress}%</strong>
            <div className="progress">
              <i style={{ width: `${p.progress}%` }} />
            </div>
            <p>Calculado automaticamente pelas tarefas concluídas.</p>
          </section>
        </div>
      )}
      {tab === 'team' && (
        <section className="panel">
          <div className="panel-head">
            <h2>Equipe do projeto</h2>
            <Button onClick={() => setMemberOpen(true)}>
              <UserPlus size={16} /> Adicionar membro
            </Button>
          </div>
          {members.data?.map((m) => (
            <div className="member-row" key={m.id}>
              <div className="avatar avatar-fallback">
                {(m.user_detail.first_name || m.user_detail.email)[0]}
              </div>
              <span>
                <b>
                  {m.user_detail.first_name} {m.user_detail.last_name}
                </b>
                <small>{m.user_detail.email}</small>
              </span>
              <em>{m.role.replaceAll('_', ' ')}</em>
              <button onClick={() => remove.mutate(m.id)}>
                <X size={17} />
              </button>
            </div>
          ))}
        </section>
      )}
      {tab === 'kanban' && <Kanban project={id} members={members.data ?? []} />}
      {tab === 'activity' && (
        <EmptyState
          title="Atividade do projeto"
          description="As atividades registradas aparecem no dashboard nesta etapa."
        />
      )}
      {!['overview', 'team', 'activity', 'kanban'].includes(tab) && (
        <EmptyState
          title="Disponível em breve"
          description="Este módulo será implementado nas próximas etapas."
        />
      )}
      {memberOpen && (
        <div className="modal-backdrop">
          <div className="form-modal">
            <div>
              <h2>Adicionar membro</h2>
              <button onClick={() => setMemberOpen(false)}>×</button>
            </div>
            <form
              onSubmit={async (e) => {
                e.preventDefault();
                await add.mutateAsync({ user: Number(user), role });
                setMemberOpen(false);
              }}
            >
              <label>
                Usuário
                <Select value={user} onChange={(e) => setUser(e.target.value)} required>
                  <option value="">Selecione</option>
                  {organizationMembers.data?.map((m) => (
                    <option value={m.user.id} key={m.id}>
                      {m.user.first_name || m.user.email}
                    </option>
                  ))}
                </Select>
              </label>
              <label>
                Função
                <Select value={role} onChange={(e) => setRole(e.target.value as ProjectRole)}>
                  <option value="PROJECT_MANAGER">Gerente</option>
                  <option value="DEVELOPER">Desenvolvedor</option>
                  <option value="DESIGNER">Designer</option>
                  <option value="MEMBER">Membro</option>
                  <option value="CLIENT">Cliente</option>
                </Select>
              </label>
              <footer>
                <Button type="button" className="secondary" onClick={() => setMemberOpen(false)}>
                  Cancelar
                </Button>
                <Button>Adicionar</Button>
              </footer>
            </form>
          </div>
        </div>
      )}
    </>
  );
}
