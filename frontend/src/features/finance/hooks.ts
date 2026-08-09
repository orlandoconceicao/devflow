import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { financeService, reportService, timeService } from '../../services/finance';
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
export const useFinanceDashboard = () =>
  useQuery({ queryKey: ['finance-dashboard'], queryFn: financeService.dashboard });
export const useExpenses = () =>
  useQuery({ queryKey: ['expenses'], queryFn: financeService.expenses });
export const useRevenues = () =>
  useQuery({ queryKey: ['revenues'], queryFn: financeService.revenues });
export const useInvoices = () =>
  useQuery({ queryKey: ['invoices'], queryFn: financeService.invoices });
export const useReport = (group: string) =>
  useQuery({ queryKey: ['report', group], queryFn: () => reportService.get(group) });
