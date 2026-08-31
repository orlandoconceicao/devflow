import { describe, expect, it } from 'vitest';
import { CORE_ROUTE_PATHS } from './App';
import routerSource from './App.tsx?raw';

describe('core application routes', () => {
  it.each([
    '/',
    '/login',
    '/register',
    '/dashboard',
    '/clients',
    '/projects',
    '/tasks',
    '/team',
    '/finance',
    '/settings',
    '/settings/billing',
  ])('keeps %s registered', (path) => {
    expect(CORE_ROUTE_PATHS).toContain(path);
    expect(routerSource).toContain(`path="${path}"`);
  });

  it('keeps redirects for the former client portal URLs', () => {
    expect(routerSource).toContain('path="/client"');
    expect(routerSource).toContain('path="/client/projects/:id"');
  });

  it('routes the root according to authentication state', () => {
    expect(routerSource).toContain("isAuthenticated ? '/dashboard' : '/login'");
    expect(routerSource).toContain('path="/" element={<RootRedirect />}');
  });
});
