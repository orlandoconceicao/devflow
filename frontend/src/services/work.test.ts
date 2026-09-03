import { describe, expect, it } from 'vitest';
import type { Organization } from '../types';
import { selectOrganization } from './work';

const organizations = [
  { id: 1, name: 'Primary' },
  { id: 2, name: 'Selected' },
] as Organization[];

describe('workspace selection regression', () => {
  it('preserves an organization explicitly selected by another admin', () => {
    expect(selectOrganization(organizations, '2')?.id).toBe(2);
  });

  it('falls back to the first accessible organization for stale selections', () => {
    expect(selectOrganization(organizations, '999')?.id).toBe(1);
  });
});
