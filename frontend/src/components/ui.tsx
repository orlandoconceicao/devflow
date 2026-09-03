import type { ButtonHTMLAttributes, InputHTMLAttributes, ReactNode } from 'react';
import { useTranslation } from '../i18n';
export function Button({ className = '', ...props }: ButtonHTMLAttributes<HTMLButtonElement>) {
  return <button className={`button ${className}`} {...props} />;
}
export function Input(props: InputHTMLAttributes<HTMLInputElement>) {
  return <input className="input" {...props} />;
}
export function LoadingState() {
  const { t } = useTranslation();
  return <div className="state">{t('Carregando')}</div>;
}
export function ErrorState({ message }: { message?: string }) {
  const { t } = useTranslation();
  return <div className="state error">{message ?? t('Não foi possível carregar.')}</div>;
}
export function EmptyState({
  title = 'Em breve',
  description = 'Estamos preparando este espaço.',
  action,
}: {
  title?: string;
  description?: string;
  action?: ReactNode;
}) {
  const { t } = useTranslation();
  return (
    <div className="empty">
      <span>✦</span>
      <h3>{t(title)}</h3>
      <p>{t(description)}</p>
      {action}
    </div>
  );
}
export function Avatar({ name, url }: { name: string; url?: string | null }) {
  return url ? (
    <img className="avatar" src={url} alt={name} />
  ) : (
    <div className="avatar avatar-fallback">{name.slice(0, 2).toUpperCase()}</div>
  );
}
export function StatusBadge({ children }: { children: ReactNode }) {
  return <span className="badge">{children}</span>;
}
export function Modal({ children }: { children: ReactNode }) {
  return (
    <div role="dialog" className="modal">
      {children}
    </div>
  );
}
export function ConfirmDialog({ children }: { children: ReactNode }) {
  return <Modal>{children}</Modal>;
}
export function Select(props: React.SelectHTMLAttributes<HTMLSelectElement>) {
  return <select className="input" {...props} />;
}
