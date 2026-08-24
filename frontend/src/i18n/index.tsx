import { createContext, useContext, type ReactNode } from 'react';
import { useAuth } from '../features/auth/AuthContext';

const messages = {
  'pt-BR': { preferences: 'Preferências', help: 'Ajuda', teamChat: 'Chat da equipe' },
  en: { preferences: 'Preferences', help: 'Help', teamChat: 'Team chat' },
} as const;
type MessageKey = keyof typeof messages['pt-BR'];
const I18nContext = createContext<(key: MessageKey) => string>((key) => key);

export function I18nProvider({ children }: { children: ReactNode }) {
  const { user } = useAuth();
  const locale = user?.language === 'en' ? 'en' : 'pt-BR';
  document.documentElement.lang = locale;
  document.documentElement.dataset.theme = user?.theme || 'system';
  if (user?.timezone) localStorage.setItem('preferred_timezone', user.timezone);
  localStorage.setItem('preferred_language', locale);
  return <I18nContext.Provider value={(key) => messages[locale][key]}>{children}</I18nContext.Provider>;
}
export const useTranslation = () => useContext(I18nContext);
