import { CalendarDays } from 'lucide-react';
import { Link } from 'react-router-dom';
import type { Project } from '../types';
import { formatDate } from '../utils/format';
const status = {
  PLANNING: 'Planejamento',
  ACTIVE: 'Ativo',
  ON_HOLD: 'Pausado',
  COMPLETED: 'Concluído',
  CANCELLED: 'Cancelado',
};
const priority = { LOW: 'Baixa', MEDIUM: 'Média', HIGH: 'Alta', URGENT: 'Urgente' };
export function ProjectCard({ project }: { project: Project }) {
  return (
    <Link className="project-card" to={`/projects/${project.id}`}>
      <div className="project-card-top">
        <span className={`status status-${project.status.toLowerCase()}`}>
          {status[project.status]}
        </span>
        <span className={`priority priority-${project.priority.toLowerCase()}`}>
          {priority[project.priority]}
        </span>
      </div>
      <h2>{project.name}</h2>
      <p>{project.client_detail.name}</p>
      <div className="progress-head">
        <span>Progresso</span>
        <b>{project.progress}%</b>
      </div>
      <div className="progress">
        <i style={{ width: `${project.progress}%` }} />
      </div>
      <footer>
        <span>
          <CalendarDays size={15} />
          {formatDate(project.due_date)}
        </span>
        <div className="avatar-stack">
          {project.members.slice(0, 3).map((m) => (
            <i key={m.id} title={m.user_detail.email}>
              {(m.user_detail.first_name || m.user_detail.email).slice(0, 1)}
            </i>
          ))}
        </div>
      </footer>
    </Link>
  );
}
