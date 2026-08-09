import { CalendarDays, MessageSquare, Paperclip } from 'lucide-react';
import type { Task } from '../types';
import { formatDate } from '../utils/format';
export function TaskCard({ task, onOpen }: { task: Task; onOpen: () => void }) {
  return (
    <article
      className="task-card"
      draggable
      onDragStart={(e) => e.dataTransfer.setData('task-id', String(task.id))}
      onClick={onOpen}
    >
      <div>
        {task.labels.map((l) => (
          <i key={l.id} style={{ background: l.color }} title={l.name} />
        ))}
      </div>
      <h3>{task.title}</h3>
      <span className={`priority priority-${task.priority.toLowerCase()}`}>{task.priority}</span>
      {task.is_overdue && <b className="overdue">Atrasada</b>}
      <footer>
        <span>
          {task.due_date && (
            <>
              <CalendarDays size={14} />
              {formatDate(task.due_date)}
            </>
          )}
        </span>
        <span>
          <MessageSquare size={14} />
          {task.comments_count}
          <Paperclip size={14} />
          {task.attachments_count}
        </span>
      </footer>
    </article>
  );
}
