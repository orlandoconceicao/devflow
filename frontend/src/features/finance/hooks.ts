import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { financeService, reportService, timeService } from '../../services/finance';
const organizationKey = () => localStorage.getItem('organization_id');
export const useTimeEntries = () =>
  useQuery({ queryKey: ['time-entries'], queryFn: timeService.list });
export const useActiveTimer = () =>
  useQuery({ queryKey: ['active-timer'], queryFn: timeService.active, refetchInterval: 30000 });
export function useStartTimer() {
  const q = useQueryClient();
  return useMutation({
    mutationFn: timeService.start,
    onSuccess: () => {
      q.invalidateQueries({ queryKey: ['active-timer'] });
      q.invalidateQueries({ queryKey: ['time-entries'] });
    },
  });
}
export function useStopTimer() {
  const q = useQueryClient();
  return useMutation({
    mutationFn: timeService.stop,
    onSuccess: () => {
      q.invalidateQueries({ queryKey: ['active-timer'] });
      q.invalidateQueries({ queryKey: ['time-entries'] });
    },
  });
}
export const useFinanceDashboard = (enabled = true) =>
  useQuery({
    queryKey: ['finance-dashboard', organizationKey()],
    queryFn: financeService.dashboard,
    enabled,
  });
export const useExpenses = (enabled = true) =>
  useQuery({
    queryKey: ['expenses', organizationKey()],
    queryFn: financeService.expenses,
    enabled,
  });
export const useRevenues = (enabled = true) =>
  useQuery({
    queryKey: ['revenues', organizationKey()],
    queryFn: financeService.revenues,
    enabled,
  });
export const useInvoices = (enabled = true) =>
  useQuery({
    queryKey: ['invoices', organizationKey()],
    queryFn: financeService.invoices,
    enabled,
  });
export function useCreateInvoice() {
  const q = useQueryClient();
  return useMutation({
    mutationFn: financeService.createInvoice,
    onSuccess: () => q.invalidateQueries({ queryKey: ['invoices'] }),
  });
}
export function useGeneratePayment() {
  const q = useQueryClient();
  return useMutation({
    mutationFn: ({ id, regenerate = false }: { id: number; regenerate?: boolean }) =>
      financeService.generatePayment(id, regenerate),
    onSuccess: () => q.invalidateQueries({ queryKey: ['invoices'] }),
  });
}
export const useReport = (group: string) =>
  useQuery({ queryKey: ['report', group], queryFn: () => reportService.get(group) });
