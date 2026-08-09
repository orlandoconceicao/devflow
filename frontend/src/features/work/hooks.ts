import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { clientService, dashboardService, projectService } from '../../services/work';
import type { Client, Project, ProjectRole } from '../../types';
export function useClients(params?: Record<string, string | number>) {
  return useQuery({ queryKey: ['clients', params], queryFn: () => clientService.list(params) });
}
export function useClient(id: number) {
  return useQuery({
    queryKey: ['client', id],
    queryFn: () => clientService.get(id),
    enabled: !!id,
  });
}
export function useProjects(params?: Record<string, string | number>) {
  return useQuery({ queryKey: ['projects', params], queryFn: () => projectService.list(params) });
}
export function useProject(id: number) {
  return useQuery({
    queryKey: ['project', id],
    queryFn: () => projectService.get(id),
    enabled: !!id,
  });
}
export function useProjectMembers(id: number) {
  return useQuery({
    queryKey: ['project-members', id],
    queryFn: () => projectService.members(id),
    enabled: !!id,
  });
}
export function useProjectActivities(id: number) {
  return useQuery({
    queryKey: ['project-activities', id],
    queryFn: () => projectService.activities(id),
    enabled: !!id,
  });
}
export function useDashboard() {
  return useQuery({ queryKey: ['dashboard'], queryFn: dashboardService.get });
}
export function useCreateClient() {
  const q = useQueryClient();
  return useMutation({
    mutationFn: (data: Partial<Client>) => clientService.create(data),
    onSuccess: () => q.invalidateQueries({ queryKey: ['clients'] }),
  });
}
export function useUpdateClient(id: number) {
  const q = useQueryClient();
  return useMutation({
    mutationFn: (data: Partial<Client>) => clientService.update(id, data),
    onSuccess: () => {
      q.invalidateQueries({ queryKey: ['clients'] });
      q.invalidateQueries({ queryKey: ['client', id] });
    },
  });
}
export function useDeleteClient() {
  const q = useQueryClient();
  return useMutation({
    mutationFn: clientService.remove,
    onSuccess: () => q.invalidateQueries({ queryKey: ['clients'] }),
  });
}
export function useCreateProject() {
  const q = useQueryClient();
  return useMutation({
    mutationFn: (data: Partial<Project>) => projectService.create(data),
    onSuccess: () => {
      q.invalidateQueries({ queryKey: ['projects'] });
      q.invalidateQueries({ queryKey: ['dashboard'] });
    },
  });
}
export function useUpdateProject(id: number) {
  const q = useQueryClient();
  return useMutation({
    mutationFn: (data: Partial<Project>) => projectService.update(id, data),
    onSuccess: () => {
      q.invalidateQueries({ queryKey: ['projects'] });
      q.invalidateQueries({ queryKey: ['project', id] });
      q.invalidateQueries({ queryKey: ['dashboard'] });
    },
  });
}
export function useAddProjectMember(id: number) {
  const q = useQueryClient();
  return useMutation({
    mutationFn: ({ user, role }: { user: number; role: ProjectRole }) =>
      projectService.addMember(id, user, role),
    onSuccess: () => {
      q.invalidateQueries({ queryKey: ['project-members', id] });
      q.invalidateQueries({ queryKey: ['project', id] });
    },
  });
}
export function useRemoveProjectMember(id: number) {
  const q = useQueryClient();
  return useMutation({
    mutationFn: (membership: number) => projectService.removeMember(id, membership),
    onSuccess: () => {
      q.invalidateQueries({ queryKey: ['project-members', id] });
      q.invalidateQueries({ queryKey: ['project', id] });
    },
  });
}
