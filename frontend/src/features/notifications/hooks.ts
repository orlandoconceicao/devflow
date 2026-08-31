import { useEffect } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '../../services/api';
import type { Notification, PaginatedResponse } from '../../types';

export const shouldUseNotificationsSocket = (configuredUrl: string | undefined, hostname: string) =>
  Boolean(configuredUrl?.trim()) || ['localhost', '127.0.0.1'].includes(hostname);

export const useNotifications = (unread = false) =>
  useQuery({
    queryKey: ['notifications', unread],
    queryFn: () =>
      api
        .get<PaginatedResponse<Notification>>('/notifications/', {
          params: unread ? { read_at__isnull: true } : {},
        })
        .then((r) => r.data),
  });
export const useUnreadCount = (enabled = true) =>
  useQuery({
    queryKey: ['notification-count'],
    queryFn: () => api.get<{ count: number }>('/notifications/unread-count/').then((r) => r.data),
    refetchInterval: 30000,
    enabled,
  });
export function useNotificationsSocket(enabled = true) {
  const q = useQueryClient();
  useEffect(() => {
    let ws: WebSocket | undefined,
      timer: number,
      attempt = 0,
      closed = false;
    const connect = () => {
      if (!enabled) return;
      const token = localStorage.getItem('access');
      if (!token || closed) return;
      const configuredBase = import.meta.env.VITE_WS_URL?.trim();
      if (!shouldUseNotificationsSocket(configuredBase, location.hostname)) return;
      const base =
        configuredBase || `${location.protocol === 'https:' ? 'wss:' : 'ws:'}//${location.host}`;
      ws = new WebSocket(`${base}/ws/notifications/?token=${token}`);
      ws.onopen = () => (attempt = 0);
      ws.onmessage = () => {
        q.invalidateQueries({ queryKey: ['notifications'] });
        q.invalidateQueries({ queryKey: ['notification-count'] });
      };
      ws.onclose = () => {
        if (!closed) timer = window.setTimeout(connect, Math.min(30000, 1000 * 2 ** attempt++));
      };
    };
    connect();
    return () => {
      closed = true;
      clearTimeout(timer);
      if (ws?.readyState === WebSocket.OPEN) {
        ws.close();
      } else if (ws?.readyState === WebSocket.CONNECTING) {
        ws.addEventListener('open', () => ws?.close(), { once: true });
      }
    };
  }, [enabled, q]);
}
