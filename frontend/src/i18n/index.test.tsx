import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const auth = vi.hoisted(() => ({
  user: null as null | { language: string; theme: string; timezone: string },
}));
vi.mock('../features/auth/AuthContext', () => ({ useAuth: () => auth }));

import { I18nProvider, useTranslation } from './index';

function Probe() {
  const { locale, t } = useTranslation();
  return (
    <span>
      {locale}:{t('Projetos')}:{t('Sair')}
    </span>
  );
}

describe('internationalization preferences', () => {
  beforeEach(() => {
    localStorage.clear();
    auth.user = null;
  });

  it('uses Portuguese by default', () => {
    render(
      <I18nProvider>
        <Probe />
      </I18nProvider>,
    );
    expect(screen.getByText('pt-BR:Projetos:Sair')).toBeInTheDocument();
    expect(document.documentElement.lang).toBe('pt-BR');
  });

  it('loads a persisted English preference before authentication', () => {
    localStorage.setItem('preferred_language', 'en');
    render(
      <I18nProvider>
        <Probe />
      </I18nProvider>,
    );
    expect(screen.getByText('en:Projects:Log out')).toBeInTheDocument();
    expect(document.documentElement.lang).toBe('en');
  });

  it('follows the authenticated preference and persists it', () => {
    auth.user = { language: 'en', theme: 'dark', timezone: 'UTC' };
    const view = render(
      <I18nProvider>
        <Probe />
      </I18nProvider>,
    );
    expect(screen.getByText('en:Projects:Log out')).toBeInTheDocument();
    expect(localStorage.getItem('preferred_language')).toBe('en');

    auth.user = { language: 'pt-BR', theme: 'light', timezone: 'America/Cuiaba' };
    view.rerender(
      <I18nProvider>
        <Probe />
      </I18nProvider>,
    );
    expect(screen.getByText('pt-BR:Projetos:Sair')).toBeInTheDocument();
    expect(localStorage.getItem('preferred_language')).toBe('pt-BR');
  });
});
