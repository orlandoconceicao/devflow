import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { renderHook, waitFor } from '@testing-library/react';
import type { ReactNode } from 'react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const services = vi.hoisted(() => ({
  dashboard: vi.fn(),
  expenses: vi.fn(),
  revenues: vi.fn(),
  invoices: vi.fn(),
}));
vi.mock('../../services/finance', () => ({
  financeService: {
    dashboard: services.dashboard,
    expenses: services.expenses,
    revenues: services.revenues,
    invoices: services.invoices,
  },
  reportService: { get: vi.fn() },
  timeService: { list: vi.fn(), active: vi.fn(), start: vi.fn(), stop: vi.fn() },
}));

import { useExpenses, useFinanceDashboard, useInvoices, useRevenues } from './hooks';

const wrapper = ({ children }: { children: ReactNode }) => (
  <QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}>
    {children}
  </QueryClientProvider>
);

describe('finance tab loading', () => {
  beforeEach(() => {
    localStorage.clear();
    localStorage.setItem('organization_id', '7');
    vi.clearAllMocks();
    services.dashboard.mockResolvedValue({ revenue: 0 });
    services.expenses.mockResolvedValue({ results: [] });
    services.revenues.mockResolvedValue({ results: [] });
    services.invoices.mockResolvedValue({ results: [] });
  });

  it('does not request inactive tabs', async () => {
    renderHook(
      () => {
        useFinanceDashboard(true);
        useExpenses(false);
        useRevenues(false);
        useInvoices(false);
      },
      { wrapper },
    );

    await waitFor(() => expect(services.dashboard).toHaveBeenCalledTimes(1));
    expect(services.expenses).not.toHaveBeenCalled();
    expect(services.revenues).not.toHaveBeenCalled();
    expect(services.invoices).not.toHaveBeenCalled();
  });
});
