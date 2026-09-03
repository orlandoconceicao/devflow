import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react';
import { api, clearAuthStorage } from '../../services/api';
import type { User } from '../../types';

let currentUserRequest: Promise<User> | null = null;

const fetchCurrentUser = () => {
  currentUserRequest ??= api
    .get<User>('/auth/me/')
    .then(({ data }) => data)
    .finally(() => {
      currentUserRequest = null;
    });
  return currentUserRequest;
};
interface AuthValue {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (data: RegisterData) => Promise<void>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
}
interface RegisterData {
  first_name: string;
  last_name: string;
  email: string;
  password: string;
  password_confirm: string;
}
const AuthContext = createContext<AuthValue | null>(null);
export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setLoading] = useState(true);
  const refreshUser = useCallback(async () => {
    try {
      setUser(await fetchCurrentUser());
    } catch {
      clearAuthStorage();
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);
  useEffect(() => {
    if (localStorage.getItem('access') || localStorage.getItem('refresh')) void refreshUser();
    else setLoading(false);
  }, [refreshUser]);
  const login = async (email: string, password: string) => {
    const { data } = await api.post<{ access: string; refresh: string; user: User }>(
      '/auth/login/',
      { email: email.trim().toLowerCase(), password },
    );
    clearAuthStorage();
    localStorage.setItem('access', data.access);
    localStorage.setItem('refresh', data.refresh);
    setUser(data.user);
  };
  const register = async (data: RegisterData) => {
    await api.post('/auth/register/', data);
    await login(data.email.trim().toLowerCase(), data.password);
  };
  const logout = async () => {
    const refresh = localStorage.getItem('refresh');
    clearAuthStorage();
    currentUserRequest = null;
    setUser(null);
    try {
      if (refresh) await api.post('/auth/logout/', { refresh });
    } catch {
      // Local logout must still complete if the token is expired or the API is offline.
    } finally {
      clearAuthStorage();
      setUser(null);
      if (window.location.pathname !== '/login') window.location.replace('/login');
    }
  };
  const value = useMemo(
    () => ({ user, isAuthenticated: !!user, isLoading, login, register, logout, refreshUser }),
    [user, isLoading, refreshUser],
  );
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
export function useAuth() {
  const value = useContext(AuthContext);
  if (!value) throw new Error('useAuth fora do provider');
  return value;
}
