import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { taskService } from '../../services/tasks';
import type { MoveTaskPayload, Task } from '../../types';
const invalidate = (q: ReturnType<typeof useQueryClient>, project?: number) => {
  q.invalidateQueries({ queryKey: ['tasks'] });
  if (project) q.invalidateQueries({ queryKey: ['project-tasks', project] });
  q.invalidateQueries({ queryKey: ['projects'] });
  q.invalidateQueries({ queryKey: ['project', project] });
  q.invalidateQueries({ queryKey: ['dashboard'] });
};
export const useTasks = (params?: Record<string, string | number | boolean>) =>
  useQuery({ queryKey: ['tasks', params], queryFn: () => taskService.list(params) });
export const useProjectTasks = (id: number) =>
  useQuery({
    queryKey: ['project-tasks', id],
    queryFn: () => taskService.projectTasks(id),
    enabled: !!id,
  });
export const useTask = (id: number) =>
  useQuery({ queryKey: ['task', id], queryFn: () => taskService.get(id), enabled: !!id });
export const useTaskLabels = () =>
  useQuery({ queryKey: ['task-labels'], queryFn: taskService.labels });
export const useTaskComments = (id: number) =>
  useQuery({
    queryKey: ['task-comments', id],
    queryFn: () => taskService.comments(id),
    enabled: !!id,
  });
export const useTaskAttachments = (id: number) =>
  useQuery({
    queryKey: ['task-attachments', id],
    queryFn: () => taskService.attachments(id),
    enabled: !!id,
  });
export const useTaskActivities = (id: number) =>
  useQuery({
    queryKey: ['task-activities', id],
    queryFn: () => taskService.activities(id),
    enabled: !!id,
  });
export function useCreateTask(project: number) {
  const q = useQueryClient();
  return useMutation({
    mutationFn: (data: Partial<Task> & { assignee_ids?: number[]; label_ids?: number[] }) =>
      taskService.create({ ...data, project }),
    onSuccess: () => invalidate(q, project),
  });
}
export function useUpdateTask(id: number, project: number) {
  const q = useQueryClient();
  return useMutation({
    mutationFn: (data: Partial<Task>) => taskService.update(id, data),
    onSuccess: () => {
      invalidate(q, project);
      q.invalidateQueries({ queryKey: ['task', id] });
    },
  });
}
export function useMoveTask(project: number) {
  const q = useQueryClient();
  return useMutation({
    mutationFn: ({ id, ...data }: { id: number } & MoveTaskPayload) => taskService.move(id, data),
    onSuccess: () => invalidate(q, project),
    onError: () => q.invalidateQueries({ queryKey: ['project-tasks', project] }),
  });
}
export function useDeleteTask(project?: number) {
  const q = useQueryClient();
  return useMutation({ mutationFn: taskService.remove, onSuccess: () => invalidate(q, project) });
}
export function useCreateComment(id: number) {
  const q = useQueryClient();
  return useMutation({
    mutationFn: (content: string) => taskService.comment(id, content),
    onSuccess: () => q.invalidateQueries({ queryKey: ['task-comments', id] }),
  });
}
export function useUploadAttachment(id: number) {
  const q = useQueryClient();
  return useMutation({
    mutationFn: (file: File) => taskService.upload(id, file),
    onSuccess: () => q.invalidateQueries({ queryKey: ['task-attachments', id] }),
  });
}
