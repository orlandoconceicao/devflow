import { Play, Square } from 'lucide-react';
import { useEffect, useState } from 'react';
import { Button, EmptyState, Input, LoadingState, Select } from '../components/ui';
import {
  useActiveTimer,
  useStartTimer,
  useStopTimer,
  useTimeEntries,
} from '../features/finance/hooks';
import { useProjects } from '../features/work/hooks';
const elapsed = (start: string) =>
  Math.max(0, Math.floor((Date.now() - new Date(start).getTime()) / 1000));
const clock = (s: number) =>
  [Math.floor(s / 3600), Math.floor((s % 3600) / 60), s % 60]
    .map((v) => String(v).padStart(2, '0'))
    .join(':');
export function TimeTracking() {
  const entries = useTimeEntries(),
    active = useActiveTimer(),
    projects = useProjects();
  const start = useStartTimer(),
    stop = useStopTimer();
  const [tick, setTick] = useState(0),
    [project, setProject] = useState(''),
    [description, setDescription] = useState('');
  useEffect(() => {
    const id = setInterval(() => setTick((x) => x + 1), 1000);
    return () => clearInterval(id);
  }, []);
  const timer = active.data;
  return (
    <>
      <div className="page-head">
        <div>
          <h1>Controle de horas</h1>
          <p>Registre o tempo real dedicado aos projetos.</p>
        </div>
      </div>
      <section className="timer-card">
        <div>
          <small>TIMER ATUAL</small>
          <strong>{timer ? clock(elapsed(timer.started_at)) : clock(0)}</strong>
          <span>{timer?.project_name || 'Nenhum timer em andamento'}</span>
        </div>
        {timer ? (
          <Button onClick={() => stop.mutate(timer.id)}>
            <Square size={17} /> Parar
          </Button>
        ) : (
          <div className="timer-form">
            <Select value={project} onChange={(e) => setProject(e.target.value)}>
              <option value="">Selecione o projeto</option>
              {projects.data?.results.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name}
                </option>
              ))}
            </Select>
            <Input
              placeholder="No que você está trabalhando?"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
            />
            <Button
              disabled={!project}
              onClick={() =>
                start.mutate({ project: Number(project), description, billable: true })
              }
            >
              <Play size={17} /> Iniciar
            </Button>
          </div>
        )}
      </section>
      <section className="panel section-gap">
        <h2>Lançamentos recentes</h2>
        {entries.isLoading ? (
          <LoadingState />
        ) : entries.data?.results.length ? (
          <div className="table-wrap flat">
            <table>
              <thead>
                <tr>
                  <th>Projeto</th>
                  <th>Descrição</th>
                  <th>Pessoa</th>
                  <th>Duração</th>
                  <th>Faturável</th>
                  <th>Data</th>
                </tr>
              </thead>
              <tbody>
                {entries.data.results.map((x) => (
                  <tr key={x.id}>
                    <td>{x.project_name}</td>
                    <td>{x.description || '—'}</td>
                    <td>{x.user_name}</td>
                    <td>{clock(x.ended_at ? x.duration_seconds : elapsed(x.started_at))}</td>
                    <td>{x.billable ? 'Sim' : 'Não'}</td>
                    <td>{new Date(x.started_at).toLocaleDateString('pt-BR')}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <EmptyState
            title="Nenhuma hora lançada"
            description="Inicie o timer para criar seu primeiro registro."
          />
        )}
      </section>
    </>
  );
}
