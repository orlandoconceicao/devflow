import { api } from './api';
import type {
  ActivityLog,
  Client,
  DashboardData,
  Organization,
  PaginatedResponse,
  Project,
  ProjectMember,
  ProjectRole,
  OrganizationMembership,
  Role,
} from '../types';

let organizationRequest: Promise<Organization | undefined> | null = null;

export const organizationService = {
  async ensure() {
    organizationRequest ??= api
      .get<PaginatedResponse<Organization>>('/organizations/')
      .then(({ data }) => {
        const organization = data.results[0];
        if (organization) localStorage.setItem('organization_id', String(organization.id));
        return organization;
      })
      .finally(() => {
        organizationRequest = null;
      });
    return organizationRequest;
  },
  members: (id: number) =>
    api.get<PaginatedResponse<OrganizationMembership>>(`/organizations/${id}/members/`).then((r) => r.data),
  invite: (id: number, data: { email: string; role: Exclude<Role, 'OWNER' | 'CLIENT'> }) =>
    api.post<{ invite_url: string }>(`/organizations/${id}/team-invitations/`, data).then((r) => r.data),
  invitations: (id: number) =>
    api.get<Array<{ id:number; email:string; role:'ADMIN'|'MEMBER'; expires_at:string; status:string }>>(`/organizations/${id}/team-invitations/`).then((r) => r.data),
  updateMember: (organizationId: number, membershipId: number, role: 'ADMIN' | 'MEMBER') =>
    api.patch<OrganizationMembership>(`/organizations/${organizationId}/members/${membershipId}/`, { role }).then((r) => r.data),
  removeMember: (organizationId: number, membershipId: number) =>
    api.delete(`/organizations/${organizationId}/members/${membershipId}/`),
  approveMember: (organizationId: number, membershipId: number) =>
    api.post<OrganizationMembership>(`/organizations/${organizationId}/members/${membershipId}/`).then((r) => r.data),
};
export const clientService = {
  list: (params?: Record<string, string | number>) =>
    api.get<PaginatedResponse<Client>>('/clients/', { params }).then((r) => r.data),
  get: (id: number) => api.get<Client>(`/clients/${id}/`).then((r) => r.data),
  create: (data: Partial<Client>) => api.post<Client>('/clients/', data).then((r) => r.data),
  update: (id: number, data: Partial<Client>) =>
    api.patch<Client>(`/clients/${id}/`, data).then((r) => r.data),
  remove: (id: number) => api.delete(`/clients/${id}/`),
};
export const projectService = {
  list: (params?: Record<string, string | number>) =>
    api.get<PaginatedResponse<Project>>('/projects/', { params }).then((r) => r.data),
  get: (id: number) => api.get<Project>(`/projects/${id}/`).then((r) => r.data),
  create: (data: Partial<Project>) => api.post<Project>('/projects/', data).then((r) => r.data),
  update: (id: number, data: Partial<Project>) =>
    api.patch<Project>(`/projects/${id}/`, data).then((r) => r.data),
  remove: (id: number) => api.delete(`/projects/${id}/`),
  members: (id: number) => api.get<ProjectMember[]>(`/projects/${id}/members/`).then((r) => r.data),
  activities: (id: number) =>
    api.get<ActivityLog[]>(`/projects/${id}/activities/`).then((r) => r.data),
  addMember: (id: number, user: number, role: ProjectRole) =>
    api.post<ProjectMember>(`/projects/${id}/members/`, { user, role }).then((r) => r.data),
  removeMember: (id: number, membership: number) =>
    api.delete(`/projects/${id}/members/${membership}/`),
};
export const dashboardService = {
  get: () => api.get<DashboardData>('/dashboard/').then((r) => r.data),
};
