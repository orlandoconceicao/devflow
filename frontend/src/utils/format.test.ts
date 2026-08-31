import { beforeEach, describe, expect, it } from 'vitest';
import { formatCurrency, formatDate } from './format';

describe('format helpers', () => {
  beforeEach(() => localStorage.clear());

  it('formats money using the preferred locale and BRL', () => {
    localStorage.setItem('preferred_language', 'pt-BR');
    expect(formatCurrency('1234.5')).toMatch(/R\$\s?1\.234,50/);
  });

  it('uses the preferred timezone without shifting date-only values', () => {
    localStorage.setItem('preferred_language', 'en-US');
    localStorage.setItem('preferred_timezone', 'America/Cuiaba');
    expect(formatDate('2026-08-31')).toBe('8/31/2026');
  });

  it('returns the product fallback for an absent due date', () => {
    expect(formatDate(null)).toBe('Sem prazo');
  });
});
