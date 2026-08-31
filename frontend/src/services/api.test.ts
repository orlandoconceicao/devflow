import { beforeEach, describe, expect, it } from 'vitest';
import { organizationIdForRequest } from './api';

describe('organization request context', () => {
  beforeEach(() => localStorage.clear());

  it('adds a valid organization only to workspace endpoints', () => {
    localStorage.setItem('organization_id', '42');
    expect(organizationIdForRequest('/dashboard/')).toBe('42');
    expect(organizationIdForRequest('/projects/')).toBe('42');
  });

  it.each(['/auth/login/', '/auth/register/', '/auth/refresh/', '/organizations/'])(
    'does not attach an organization to %s',
    (url) => {
      localStorage.setItem('organization_id', '42');
      expect(organizationIdForRequest(url)).toBeNull();
    },
  );

  it.each(['', 'null', 'undefined', 'invalid', '-1'])(
    'rejects invalid organization value %s',
    (value) => {
      localStorage.setItem('organization_id', value);
      expect(organizationIdForRequest('/dashboard/')).toBeNull();
    },
  );
});
