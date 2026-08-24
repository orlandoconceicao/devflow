import { Search } from 'lucide-react';
import { useState } from 'react';
import { useAuth } from '../features/auth/AuthContext';
import { useProjects } from '../features/work/hooks';
import { useTasks } from '../features/tasks/hooks';
import { TaskDetails } from '../components/Kanban';
import { Button, EmptyState, ErrorState, LoadingState, Select } from '../components/ui';
import { Link } from 'react-router-dom';
import type { TaskStatus } from '../types';
import { formatDate } from '../utils/format';
const status: Record<TaskStatus, string> = {
  BACKLOG: 'Backlog',
  TODO: 'A fazer',
  IN_PROGRESS: 'Em andamento',
  REVIEW: 'Revisão',
  DONE: 'Concluída',
};
export function TasksPage() {
  const { user } = useAuth();
  const [search, setSearch] = useState('');
  const [project, setProject] = useState('');
  const [taskStatus, setStatus] = useState('');
  const [priority, setPriority] = useState('');
  const [mine, setMine] = useState(false);
  const [selected, setSelected] = useState<number | null>(null);
  const [page, setPage] = useState(1);
  const tasks = useTasks({
    search,
    project,
    status: taskStatus,
    priority,
    page,
    ...(mine && user ? { assignees__user: user.id } : {}),
  });
  const projects = useProjects();
  return (
    <>
      <div className="page-head">
        <div>
          <h1>Tarefas</h1>
          <p>Acompanhe o trabalho de todos os seus projetos.</p>
        </div>
      </div>
      <div className="quick-filters">
        <button className={mine ? 'active' : ''} onClick={() => setMine(!mine)}>
          Minhas tarefas
        </button>
        <button onClick={() => setStatus('TODO')}>Pendentes</button>
        <button onClick={() => setStatus('DONE')}>Concluídas</button>
      </div>
      <div className="toolbar task-toolbar">
        <div className="search-field">
          <Search size={17} />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Buscar tarefas…"
          />
        </div>
        <Select value={project} onChange={(e) => setProject(e.target.value)}>
          <option value="">Todos os projetos</option>
          {projects.data?.results.map((p) => (
            <option key={p.id} value={p.id}>
              {p.name}
            </option>
          ))}
        </Select>
        <Select value={taskStatus} onChange={(e) => setStatus(e.target.value)}>
          <option value="">Todos os status</option>
          {Object.entries(status).map(([v, l]) => (
            <option value={v} key={v}>
              {l}
            </option>
          ))}
        </Select>
        <Select value={priority} onChange={(e) => setPriority(e.target.value)}>
          <option value="">Prioridades</option>
          <option value="LOW">Baixa</option>
          <option value="MEDIUM">Média</option>
          <option value="HIGH">Alta</option>
          <option value="URGENT">Urgente</option>
        </Select>
      </div>
      {tasks.isLoading ? (
        <LoadingState />
      ) : tasks.isError ? (
        <ErrorState message="Não foi possível carregar as tarefas." />
      ) : !tasks.data?.results.length ? (
        <EmptyState
          title="Nenhuma tarefa encontrada"
          description="Ajuste os filtros ou crie uma tarefa pelo Kanban do projeto."
          action={projects.data?.results.length ? <Link className="button" to={`/projects/${projects.data.results[0].id}`}>Abrir projeto e criar tarefa</Link> : <Link className="button" to="/projects?new=1">Criar projeto</Link>}
        />
      ) : (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Tarefa</th>
                <th>Projeto</th>
                <th>Status</th>
                <th>Prioridade</th>
                <th>Responsáveis</th>
                <th>Prazo</th>
                <th>Labels</th>
              </tr>
            </thead>
            <tbody>
              {tasks.data.results.map((t) => (
                <tr key={t.id} onClick={() => setSelected(t.id)} className="clickable">
                  <td>
                    <b>{t.title}</b>
                    {t.is_overdue && <small className="overdue">Atrasada</small>}
                  </td>
                  <td>{t.project_name}</td>
                  <td>
                    <span className={`status status-${t.status.toLowerCase()}`}>
                      {status[t.status]}
                    </span>
                  </td>
                  <td>
                    <span className={`priority priority-${t.priority.toLowerCase()}`}>
                      {t.priority}
                    </span>
                  </td>
                  <td>
                    {t.assignees.map((a) => a.user.first_name || a.user.email).join(', ') || '—'}
                  </td>
                  <td>{formatDate(t.due_date)}</td>
                  <td>
                    {t.labels.map((l) => (
                      <i
                        className="label-dot"
                        key={l.id}
                        style={{ background: l.color }}
                        title={l.name}
                      />
                    ))}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      {!!tasks.data?.count && tasks.data.count > tasks.data.results.length && <nav className="pagination" aria-label="Paginação de tarefas"><Button className="secondary" disabled={!tasks.data.previous} onClick={() => setPage((value) => Math.max(1, value - 1))}>Anterior</Button><span>Página {page}</span><Button className="secondary" disabled={!tasks.data.next} onClick={() => setPage((value) => value + 1)}>Próxima</Button></nav>}
      {selected && (
        <TaskDetails
          taskId={selected}
          project={tasks.data?.results.find((t) => t.id === selected)?.project ?? 0}
          members={[]}
          onClose={() => setSelected(null)}
        />
      )}
    </>
  );
}
