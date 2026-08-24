export type Role = 'OWNER' | 'ADMIN' | 'MEMBER' | 'CLIENT';
export interface User {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  avatar: string | null;
}
export interface Organization {
  id: number;
  name: string;
  slug: string;
  owner: number;
  role: Role;
}
export interface OrganizationMembership {
  id: number;
  user: User;
  role: Role;
  joined_at: string;
}
export interface Plan {
  id: number;
  name: string;
  slug: string;
  price: string;
  billing_interval: 'MONTHLY';
}
export type SubscriptionStatus = 'INACTIVE' | 'ACTIVE' | 'PAST_DUE' | 'CANCELED';
export interface Subscription {
  id: number;
  organization: number;
  plan: Plan;
  status: SubscriptionStatus;
  current_period_start: string | null;
  current_period_end: string | null;
  cancel_at_period_end: boolean;
  canceled_at?: string | null;
}
export interface SubscriptionPayment {
  id: number;
  provider_payment_id: string;
  amount: string;
  currency: string;
  status: string;
  paid_at: string | null;
  created_at: string;
}
export interface AuthTokens {
  access: string;
  refresh: string;
}
export interface ApiError {
  error: { code: string; details: unknown };
}
export type ClientStatus = 'ACTIVE' | 'INACTIVE' | 'LEAD';
export interface Client {
  id: number;
  name: string;
  email: string;
  phone: string;
  company: string;
  document: string;
  website: string;
  notes: string;
  status: ClientStatus;
  project_count: number;
  created_at: string;
  updated_at: string;
}
export type ProjectStatus = 'PLANNING' | 'ACTIVE' | 'ON_HOLD' | 'COMPLETED' | 'CANCELLED';
export type ProjectPriority = 'LOW' | 'MEDIUM' | 'HIGH' | 'URGENT';
export type ProjectRole = 'PROJECT_MANAGER' | 'DEVELOPER' | 'DESIGNER' | 'MEMBER' | 'CLIENT';
export interface ProjectMember {
  id: number;
  user: number;
  user_detail: User;
  role: ProjectRole;
  joined_at: string;
}
export interface Project {
  id: number;
  client: number;
  client_detail: Client;
  name: string;
  description: string;
  status: ProjectStatus;
  priority: ProjectPriority;
  start_date: string | null;
  due_date: string | null;
  progress: number;
  budget: string | null;
  members: ProjectMember[];
  created_by: number;
  created_by_detail: User;
  created_at: string;
  updated_at: string;
}
export interface ActivityLog {
  id: number;
  user: User | null;
  action: string;
  entity_type: string;
  entity_id: number;
  metadata: Record<string, unknown>;
  created_at: string;
}
export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}
export interface DashboardData {
  active_projects: number;
  pending_tasks: number;
  hours_this_month: number;
  monthly_revenue: string;
  recent_projects: Project[];
  upcoming_deadlines: Project[];
  recent_activity: ActivityLog[];
}
export type TaskStatus = 'BACKLOG' | 'TODO' | 'IN_PROGRESS' | 'REVIEW' | 'DONE';
export type TaskPriority = 'LOW' | 'MEDIUM' | 'HIGH' | 'URGENT';
export interface TaskLabel {
  id: number;
  name: string;
  color: string;
  created_at: string;
}
export interface TaskAssignee {
  id: number;
  user: User;
  assigned_at: string;
}
export interface Task {
  id: number;
  project: number;
  project_name: string;
  title: string;
  description: string;
  status: TaskStatus;
  priority: TaskPriority;
  position: number;
  due_date: string | null;
  completed_at: string | null;
  assignees: TaskAssignee[];
  labels: TaskLabel[];
  comments_count: number;
  attachments_count: number;
  is_overdue: boolean;
  created_by?: User;
  created_at: string;
  updated_at: string;
}
export interface TaskComment {
  id: number;
  task: number;
  author: User;
  content: string;
  created_at: string;
  updated_at: string;
}
export interface TaskAttachment {
  id: number;
  task: number;
  uploaded_by: User;
  original_name: string;
  file_size: number;
  content_type: string;
  created_at: string;
  download_url: string;
}
export interface MoveTaskPayload {
  status: TaskStatus;
  position: number;
}
export interface TimeEntry {
  id: number;
  project: number;
  project_name: string;
  task: number | null;
  task_title: string | null;
  user: number;
  user_name: string;
  description: string;
  started_at: string;
  ended_at: string | null;
  duration_seconds: number;
  hourly_rate: string;
  hourly_cost: string;
  billable: boolean;
  created_at: string;
  updated_at: string;
}
export interface FinanceDashboard {
  revenue: string;
  expenses: string;
  labor_cost: string;
  profit: string;
  hours: number;
  by_project: { project__name: string; seconds: number }[];
}
export interface Expense {
  id: number;
  project: number | null;
  description: string;
  amount: string;
  category: 'SOFTWARE' | 'PEOPLE' | 'TAX' | 'MARKETING' | 'OTHER';
  occurred_on: string;
  created_by: number;
  created_at: string;
}
export interface Revenue {
  id: number;
  project: number | null;
  client: number | null;
  description: string;
  amount: string;
  occurred_on: string;
  created_by: number;
  created_at: string;
}
export interface Invoice {
  id: number;
  client: number;
  client_name: string;
  number: string;
  status: 'DRAFT' | 'SENT' | 'PAID' | 'CANCELLED';
  issued_on: string;
  due_on: string;
  total: string;
}
export interface ReportData {
  group: string;
  rows: { name: string; hours: number }[];
}
export interface Notification {
  id: number;
  type: string;
  title: string;
  message: string;
  data: Record<string, unknown>;
  read_at: string | null;
  created_at: string;
}
export interface PortalDashboard {
  active_projects: number;
  pending_deliverables: number;
  projects: Project[];
}
export interface Deliverable {
  id: number;
  project: number;
  project_name: string;
  title: string;
  description: string;
  status: string;
  due_date: string | null;
  comments: { id: number; author_name: string; message: string; created_at: string }[];
  attachments: { id: number; original_name: string }[];
}
