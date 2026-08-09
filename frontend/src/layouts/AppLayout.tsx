import {
  Bell,
  BriefcaseBusiness,
  CheckSquare,
  ChevronDown,
  CircleHelp,
  Clock3,
  LayoutDashboard,
  Menu,
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
const links = [
  ['/dashboard', 'Dashboard', LayoutDashboard],
  ['/projects', 'Projetos', BriefcaseBusiness],
  ['/tasks', 'Tarefas', CheckSquare],
  ['/time', 'Horas', Clock3],
  ['/clients', 'Clientes', Users],
  ['/team', 'Equipe', Users],
  ['/finance', 'Financeiro', WalletCards],
  ['/reports', 'Relatórios', Clock3],
  ['/client', 'Portal do cliente', BriefcaseBusiness],
] as const;
export function AppLayout() {
  const [open, setOpen] = useState(false);
  const [workspace, setWorkspace] = useState<'loading' | 'present' | 'missing' | 'error'>(
    'loading',
  );
  const { user } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const hasWorkspace = workspace === 'present';
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
          setWorkspace('present');
          return;
        }
        localStorage.removeItem('organization_id');
        setWorkspace('missing');
        if (!location.pathname.startsWith('/onboarding')) {
          navigate('/onboarding/workspace', { replace: true });
        }
      })
      .catch(() => {
        if (active) setWorkspace('error');
      });
    return () => {
      active = false;
    };
  }, [location.pathname, navigate]);
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
          {links.map(([to, label, Icon]) => (
            <NavLink key={to} to={to} onClick={() => setOpen(false)}>
              <Icon size={18} />
              {label}
            </NavLink>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <NavLink to="/settings/profile">
            <Settings size={18} />
            Configurações
          </NavLink>
          <NavLink to="/settings/notifications">
            <Bell size={18} />
            Preferências
          </NavLink>
          <a href="#help">
            <CircleHelp size={18} />
            Ajuda
          </a>
          <div className="profile">
            <Avatar name={user?.first_name || 'U'} url={user?.avatar} />
            <span>
              {user?.first_name}
              <small>{user?.email}</small>
            </span>
            <ChevronDown size={15} />
          </div>
        </div>
      </aside>
      <main>
        <header className="topbar">
          <div className="search">
            <Search size={18} />
            <input placeholder="Buscar no DevFlow…" />
          </div>
          <Link className="bell-link" to="/notifications" aria-label="Notificações">
            <Bell size={20} />
            {!!unread.data?.count && <b>{unread.data.count}</b>}
          </Link>
          <Avatar name={user?.first_name || 'U'} url={user?.avatar} />
        </header>
        <div className="content">
          {workspace === 'loading' ? (
            <LoadingState />
          ) : workspace === 'error' ? (
            <div className="form-error">Não foi possível carregar o workspace.</div>
          ) : workspace === 'missing' && !location.pathname.startsWith('/onboarding') ? (
            <LoadingState />
          ) : (
            <Outlet />
          )}
        </div>
      </main>
    </div>
  );
}
