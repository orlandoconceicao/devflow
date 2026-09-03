import { createContext, useContext, useEffect, useMemo, type ReactNode } from 'react';
import { useAuth } from '../features/auth/AuthContext';

const en: Record<string, string> = {
  Dashboard: 'Dashboard',
  Projetos: 'Projects',
  Tarefas: 'Tasks',
  Horas: 'Time',
  Clientes: 'Clients',
  Equipe: 'Team',
  'Chat da equipe': 'Team chat',
  Financeiro: 'Finance',
  Relatórios: 'Reports',
  Configurações: 'Settings',
  Preferências: 'Preferences',
  Ajuda: 'Help',
  Sair: 'Log out',
  'Buscar no DevFlow…': 'Search DevFlow…',
  Notificações: 'Notifications',
  Carregando: 'Loading…',
  'Não foi possível carregar.': 'Unable to load.',
  'Em breve': 'Coming soon',
  'Estamos preparando este espaço.': 'We are preparing this space.',
};
type I18nValue = { locale: 'pt-BR' | 'en'; t: (text: string) => string };
const I18nContext = createContext<I18nValue>({ locale: 'pt-BR', t: (text) => text });

export function I18nProvider({ children }: { children: ReactNode }) {
  const { user } = useAuth();
  const stored = localStorage.getItem('preferred_language');
  const locale = user?.language === 'en' || (!user && stored === 'en') ? 'en' : 'pt-BR';
  useEffect(() => {
    document.documentElement.lang = locale;
    document.documentElement.dataset.theme = user?.theme || 'system';
    if (user?.timezone) localStorage.setItem('preferred_timezone', user.timezone);
    localStorage.setItem('preferred_language', locale);
  }, [locale, user?.theme, user?.timezone]);
  const value = useMemo<I18nValue>(
    () => ({ locale, t: (text) => (locale === 'en' ? (en[text] ?? text) : text) }),
    [locale],
  );
  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>;
}
export const useTranslation = () => useContext(I18nContext);
