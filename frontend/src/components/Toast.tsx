import { createContext, useCallback, useContext, useMemo, useState, type ReactNode } from 'react';

type ToastKind = 'success' | 'error' | 'warning' | 'info';
type Toast = { id: number; message: string; kind: ToastKind };
const ToastContext = createContext<((message: string, kind?: ToastKind) => void) | null>(null);

export function ToastProvider({ children }: { children: ReactNode }) {
  const [items, setItems] = useState<Toast[]>([]);
  const show = useCallback((message: string, kind: ToastKind = 'success') => {
    const id = Date.now() + Math.random();
    setItems((current) => [...current, { id, message, kind }]);
    window.setTimeout(() => setItems((current) => current.filter((item) => item.id !== id)), 3500);
  }, []);
  const value = useMemo(() => show, [show]);
  return <ToastContext.Provider value={value}>{children}<div className="toast-region" aria-live="polite">{items.map((item) => <div className={`toast toast-${item.kind}`} key={item.id}>{item.message}</div>)}</div></ToastContext.Provider>;
}

export function useToast() {
  const value = useContext(ToastContext);
  if (!value) throw new Error('useToast fora do provider');
  return value;
}
