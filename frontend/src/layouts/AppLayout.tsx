import {
  Bell,
  BriefcaseBusiness,
  CheckSquare,
  ChevronDown,
  CircleHelp,
  Clock3,
  LayoutDashboard,
  Menu,
  MessageCircle,
  LogOut,
  Search,
  Settings,
  Users,
  WalletCards,
  X,
} from 'lucide-react';
import { useEffect, useState } from 'react';
import { Link, NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../features/auth/AuthContext';
import { Avatar, LoadingState } from '../components/ui';
import { organizationService } from '../services/work';
import { useNotificationsSocket, useUnreadCount } from '../features/notifications/hooks';
import type { Role } from '../types';
import { useTranslation } from '../i18n';
const workspaceLinks = [
  ['/dashboard', 'Dashboard', LayoutDashboard],
  ['/projects', 'Projetos', BriefcaseBusiness],
  ['/tasks', 'Tarefas', CheckSquare],
  ['/time', 'Horas', Clock3],
  ['/clients', 'Clientes', Users],
  ['/team', 'Equipe', Users],
  ['/team/chat', 'Chat da equipe', MessageCircle],
  ['/finance', 'Financeiro', WalletCards],
  ['/reports', 'Relatórios', Clock3],
] as const;
const clientLinks = [['/client-portal', 'Portal do cliente', BriefcaseBusiness]] as const;
const linksForRole = (role: Role | null) => {
  if (role === 'OWNER') return workspaceLinks;
  if (role === 'ADMIN') return workspaceLinks.filter(([to]) => to !== '/team');
  return workspaceLinks.filter(([to]) =>
    ['/dashboard', '/projects', '/tasks', '/time', '/reports', '/team/chat'].includes(to),
  );
};
export function AppLayout() {
  const [open, setOpen] = useState(false);
  const [workspace, setWorkspace] = useState<'loading' | 'present' | 'missing' | 'error'>(
    'loading',
  );
  const [role, setRole] = useState<Role | null>(null);
  const { user, logout } = useAuth();
  const { t } = useTranslation();
  const location = useLocation();
  const navigate = useNavigate();
  const hasWorkspace = workspace === 'present';
  const isClientRoute =
    location.pathname === '/client-portal' || location.pathname.startsWith('/client-portal/');
  const isClientCommonRoute =
    location.pathname === '/notifications' ||
    location.pathname === '/settings/profile' ||
    location.pathname.startsWith('/settings') ||
    location.pathname === '/help';
  const isAccountRoute = location.pathname.startsWith('/settings') || location.pathname === '/help';
  const roleRouteMismatch =
    role !== null &&
    ((role === 'CLIENT' && !isClientRoute && !isClientCommonRoute) ||
      (role !== 'CLIENT' && isClientRoute));
  const unread = useUnreadCount(hasWorkspace);
  useNotificationsSocket(hasWorkspace);
  useEffect(() => {
    let active = true;
    setWorkspace('loading');
    organizationService
      .ensure()
      .then((organization) => {
        if (!active) return;
        if (organization) {
          setRole(organization.role);
          setWorkspace('present');
          if (organization.role === 'CLIENT' && !isClientRoute && !isClientCommonRoute) {
            navigate('/client-portal', { replace: true });
          } else if (organization.role !== 'CLIENT' && isClientRoute) {
            navigate('/dashboard', { replace: true });
          }
          return;
        }
        localStorage.removeItem('organization_id');
        setWorkspace('missing');
        if (!location.pathname.startsWith('/onboarding') && !isAccountRoute) {
          navigate('/onboarding/workspace', { replace: true });
        }
      })
      .catch(() => {
        if (active) setWorkspace('error');
      });
    return () => {
      active = false;
    };
  }, [location.pathname, navigate, isAccountRoute]);
  return (
    <div className="shell">
      <button className="mobile-menu" onClick={() => setOpen(!open)}>
        {open ? <X /> : <Menu />}
      </button>
      <aside className={open ? 'open' : ''}>
        <div className="logo">
          <i>⌁</i>DevFlow
        </div>
        <nav>
          {(role === 'CLIENT' ? clientLinks : linksForRole(role)).map(([to, label, Icon]) => (
            <NavLink key={to} to={to} onClick={() => setOpen(false)}>
              <Icon size={18} />
              {t(label)}
            </NavLink>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <NavLink to="/settings">
            <Settings size={18} />
            {t('Configurações')}
          </NavLink>
          <NavLink to="/settings/preferences">
            <Bell size={18} />
            {t('Preferências')}
          </NavLink>
          <NavLink to="/help">
            <CircleHelp size={18} />
            {t('Ajuda')}
          </NavLink>
          <button className="sidebar-action" onClick={() => void logout()}>
            <LogOut size={18} />
            {t('Sair')}
          </button>
          <Link className="profile" to="/settings/profile">
            <Avatar name={user?.first_name || 'U'} url={user?.avatar} />
            <span>
              {user?.first_name}
              <small>{user?.email}</small>
            </span>
            <ChevronDown size={15} />
          </Link>
        </div>
      </aside>
      <main>
        <header className="topbar">
          <div className="search">
            <Search size={18} />
            <input placeholder={t('Buscar no DevFlow…')} />
          </div>
          <Link className="bell-link" to="/notifications" aria-label={t('Notificações')}>
            <Bell size={20} />
            {!!unread.data?.count && <b>{unread.data.count}</b>}
          </Link>
          <Link to="/settings/profile" aria-label="Abrir perfil">
            <Avatar name={user?.first_name || 'U'} url={user?.avatar} />
          </Link>
        </header>
        <div className="content">
          {workspace === 'loading' || roleRouteMismatch ? (
            <LoadingState />
          ) : workspace === 'error' ? (
            <div className="form-error">Não foi possível carregar o workspace.</div>
          ) : workspace === 'missing' &&
            !location.pathname.startsWith('/onboarding') &&
            !isAccountRoute ? (
            <LoadingState />
          ) : (
            <Outlet />
          )}
        </div>
      </main>
    </div>
  );
}
