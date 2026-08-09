import { useState } from 'react';
import { Button, EmptyState, LoadingState } from '../components/ui';
import { useNotifications } from '../features/notifications/hooks';
import { api } from '../services/api';
export function NotificationsPage() {
  const [unread, setUnread] = useState(false),
    items = useNotifications(unread);
  const refresh = () => items.refetch();
  return (
    <>
      <div className="page-head">
        <div>
          <h1>Notificações</h1>
          <p>Acompanhe atividades importantes do seu workspace.</p>
        </div>
        <Button
          className="secondary"
          onClick={async () => {
            await api.post('/notifications/read-all/');
            refresh();
          }}
        >
          Marcar todas como lidas
        </Button>
      </div>
      <div className="quick-filters">
        <button className={!unread ? 'active' : ''} onClick={() => setUnread(false)}>
          Todas
        </button>
        <button className={unread ? 'active' : ''} onClick={() => setUnread(true)}>
          Não lidas
        </button>
      </div>
      <section className="panel">
        {items.isLoading ? (
          <LoadingState />
        ) : items.data?.results.length ? (
          items.data.results.map((n) => (
            <button
              className={`notification-row ${n.read_at ? '' : 'unread'}`}
              key={n.id}
              onClick={async () => {
                if (!n.read_at) await api.post(`/notifications/${n.id}/read/`);
                refresh();
              }}
            >
              <i />
              <span>
                <b>{n.title}</b>
                <small>{n.message}</small>
              </span>
              <time>{new Date(n.created_at).toLocaleString('pt-BR')}</time>
            </button>
          ))
        ) : (
          <EmptyState title="Nenhuma notificação" />
        )}
      </section>
    </>
  );
}
