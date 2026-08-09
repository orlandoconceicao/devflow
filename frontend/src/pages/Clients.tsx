import { zodResolver } from '@hookform/resolvers/zod';
import { Eye, Plus, Search, Trash2 } from 'lucide-react';
import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { Link, useParams } from 'react-router-dom';
import { z } from 'zod';
import { Button, EmptyState, ErrorState, Input, LoadingState, Select } from '../components/ui';
import {
  useClient,
  useClients,
  useCreateClient,
  useDeleteClient,
  useProjects,
} from '../features/work/hooks';
import { formatDate } from '../utils/format';
const schema = z.object({
  name: z.string().min(2, 'Informe o nome'),
  company: z.string().optional(),
  email: z.union([z.literal(''), z.email('Email inválido')]),
  phone: z.string().optional(),
  document: z.string().optional(),
  website: z.union([z.literal(''), z.url('URL inválida')]),
  status: z.enum(['ACTIVE', 'INACTIVE', 'LEAD']),
  notes: z.string().optional(),
});
type Form = z.infer<typeof schema>;
export function ClientsPage() {
  const [search, setSearch] = useState('');
  const [status, setStatus] = useState('');
  const [open, setOpen] = useState(false);
  const clients = useClients({ search, status });
  const create = useCreateClient();
  const remove = useDeleteClient();
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<Form>({
    resolver: zodResolver(schema),
    defaultValues: {
      name: '',
      company: '',
      email: '',
      phone: '',
      document: '',
      website: '',
      status: 'ACTIVE',
      notes: '',
    },
  });
  return (
    <>
      <div className="page-head">
        <div>
          <h1>Clientes</h1>
          <p>Gerencie seus clientes e empresas.</p>
        </div>
        <Button onClick={() => setOpen(true)}>
          <Plus size={18} /> Novo cliente
        </Button>
      </div>
      <div className="toolbar">
        <div className="search-field">
          <Search size={17} />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Buscar clientes…"
          />
        </div>
        <Select value={status} onChange={(e) => setStatus(e.target.value)}>
          <option value="">Todos os status</option>
          <option value="ACTIVE">Ativos</option>
          <option value="LEAD">Leads</option>
          <option value="INACTIVE">Inativos</option>
        </Select>
      </div>
      {clients.isLoading ? (
        <LoadingState />
      ) : clients.isError ? (
        <ErrorState message="Não foi possível carregar os clientes." />
      ) : !clients.data?.results.length ? (
        <EmptyState
          title="Você ainda não possui clientes"
          description="Cadastre seu primeiro cliente para começar a organizar seus projetos."
        />
      ) : (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Cliente</th>
                <th>Empresa</th>
                <th>Email</th>
                <th>Telefone</th>
                <th>Status</th>
                <th>Projetos</th>
                <th>Criado em</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {clients.data.results.map((c) => (
                <tr key={c.id}>
                  <td>
                    <b>{c.name}</b>
                  </td>
                  <td>{c.company || '—'}</td>
                  <td>{c.email || '—'}</td>
                  <td>{c.phone || '—'}</td>
                  <td>
                    <span className={`status status-${c.status.toLowerCase()}`}>
                      {c.status === 'ACTIVE' ? 'Ativo' : c.status === 'LEAD' ? 'Lead' : 'Inativo'}
                    </span>
                  </td>
                  <td>{c.project_count}</td>
                  <td>{new Date(c.created_at).toLocaleDateString('pt-BR')}</td>
                  <td className="actions">
                    <Link to={`/clients/${c.id}`} aria-label="Visualizar">
                      <Eye size={17} />
                    </Link>
                    <button
                      aria-label="Excluir"
                      onClick={() => {
                        if (confirm(`Excluir ${c.name}?`)) remove.mutate(c.id);
                      }}
                    >
                      <Trash2 size={17} />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      {open && (
        <div className="modal-backdrop">
          <div className="form-modal">
            <div>
              <h2>Novo cliente</h2>
              <button onClick={() => setOpen(false)}>×</button>
            </div>
            <form
              onSubmit={handleSubmit(async (v) => {
                await create.mutateAsync(v);
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
                  Empresa
                  <Input {...register('company')} />
                </label>
              </div>
              <div className="form-row">
                <label>
                  Email
                  <Input type="email" {...register('email')} />
                  <small>{errors.email?.message}</small>
                </label>
                <label>
                  Telefone
                  <Input {...register('phone')} />
                </label>
              </div>
              <div className="form-row">
                <label>
                  Documento
                  <Input {...register('document')} />
                </label>
                <label>
                  Website
                  <Input {...register('website')} />
                  <small>{errors.website?.message}</small>
                </label>
              </div>
              <label>
                Status
                <Select {...register('status')}>
                  <option value="ACTIVE">Ativo</option>
                  <option value="LEAD">Lead</option>
                  <option value="INACTIVE">Inativo</option>
                </Select>
              </label>
              <label>
                Observações
                <textarea {...register('notes')} />
              </label>
              <footer>
                <Button type="button" className="secondary" onClick={() => setOpen(false)}>
                  Cancelar
                </Button>
                <Button disabled={isSubmitting}>Salvar cliente</Button>
              </footer>
            </form>
          </div>
        </div>
      )}
    </>
  );
}
export function ClientDetail() {
  const id = Number(useParams().id);
  const client = useClient(id);
  const projects = useProjects({ client: id });
  if (client.isLoading) return <LoadingState />;
  if (!client.data) return <ErrorState />;
  const c = client.data;
  return (
    <>
      <div className="page-head">
        <div>
          <span className={`status status-${c.status.toLowerCase()}`}>{c.status}</span>
          <h1>{c.name}</h1>
          <p>{c.company || 'Cliente independente'}</p>
        </div>
      </div>
      <div className="detail-grid">
        <section className="panel">
          <h2>Informações</h2>
          <dl>
            <dt>Email</dt>
            <dd>{c.email || 'Não informado'}</dd>
            <dt>Telefone</dt>
            <dd>{c.phone || 'Não informado'}</dd>
            <dt>Website</dt>
            <dd>{c.website ? <a href={c.website}>{c.website}</a> : 'Não informado'}</dd>
            <dt>Documento</dt>
            <dd>{c.document || 'Não informado'}</dd>
            <dt>Criado em</dt>
            <dd>{formatDate(c.created_at.slice(0, 10))}</dd>
          </dl>
        </section>
        <section className="panel">
          <h2>Observações</h2>
          <p>{c.notes || 'Nenhuma observação cadastrada.'}</p>
        </section>
      </div>
      <section className="panel section-gap">
        <h2>Projetos</h2>
        {projects.data?.results.length ? (
          projects.data.results.map((p) => (
            <Link className="project-row" to={`/projects/${p.id}`} key={p.id}>
              <b>{p.name}</b>
              <span>{p.progress}%</span>
            </Link>
          ))
        ) : (
          <EmptyState
            title="Nenhum projeto"
            description="Este cliente ainda não possui projetos."
          />
        )}
      </section>
    </>
  );
}
