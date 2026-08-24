import { Navigate, Route, Routes, useLocation } from 'react-router-dom';
import type { ReactNode } from 'react';
import { LoadingState } from './components/ui';
import { useAuth } from './features/auth/AuthContext';
import { AppLayout } from './layouts/AppLayout';
import {
  LoginPage,
  PasswordResetConfirmPage,
  PasswordResetPage,
  RegisterPage,
} from './pages/AuthPages';
import { Dashboard } from './pages/Dashboard';
import { PlanPage, WorkspacePage } from './pages/Onboarding';
import { BillingPage, NotificationSettings, ProfilePage } from './pages/Settings';
import { ClientDetail, ClientsPage } from './pages/Clients';
import { ProjectDetail, ProjectsPage } from './pages/Projects';
import { TasksPage } from './pages/Tasks';
import { TimeTracking } from './pages/TimeTracking';
import { FinancePage } from './pages/Finance';
import { ReportsPage } from './pages/Reports';
import { NotificationsPage } from './pages/Notifications';
import { AcceptClientInvitation, ClientPortal, ClientProject } from './pages/ClientPortal';
import { BillingResult, PricingPage } from './pages/Pricing';
import { NotFoundPage } from './pages/Errors';
import { PublicPaymentPage } from './pages/PublicPayment';
import { TeamPage } from './pages/Team';
import { TeamInvitationPage } from './pages/TeamInvitation';
import { HelpPage, PreferencesPage, SettingsHome, TeamChatPage } from './pages/AccountPages';
function Protected() {
  const { isAuthenticated, isLoading } = useAuth();
  if (isLoading) return <LoadingState />;
  return isAuthenticated ? <AppLayout /> : <Navigate to="/login" replace />;
}
function ProtectedPage({ children }: { children: ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth();
  const location = useLocation();
  if (isLoading) return <LoadingState />;
  const returnTo = `${location.pathname}${location.search}`;
  return isAuthenticated ? (
    children
  ) : (
    <Navigate to={`/login?next=${encodeURIComponent(returnTo)}`} replace />
  );
}
export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/login" replace />} />

      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route path="/password-reset" element={<PasswordResetPage />} />
      <Route path="/password-reset/confirm" element={<PasswordResetConfirmPage />} />
      <Route path="/pagar/:token" element={<PublicPaymentPage />} />
      <Route path="/team-invitations/accept" element={<TeamInvitationPage />} />

      <Route
        path="/client-invitations/accept"
        element={
          <ProtectedPage>
            <AcceptClientInvitation />
          </ProtectedPage>
        }
      />

      <Route element={<Protected />}>
        <Route path="/onboarding" element={<Navigate to="/onboarding/workspace" />} />
        <Route path="/onboarding/workspace" element={<WorkspacePage />} />
        <Route path="/onboarding/plan" element={<PlanPage />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/clients" element={<ClientsPage />} />
        <Route path="/clients/:id" element={<ClientDetail />} />
        <Route path="/projects" element={<ProjectsPage />} />
        <Route path="/projects/:id" element={<ProjectDetail />} />
        <Route path="/tasks" element={<TasksPage />} />
        <Route path="/time" element={<TimeTracking />} />
        <Route path="/finance" element={<FinancePage />} />
        <Route path="/reports" element={<ReportsPage />} />
        <Route path="/team" element={<TeamPage />} />
        <Route path="/team/chat" element={<TeamChatPage />} />
        <Route path="/notifications" element={<NotificationsPage />} />
        <Route path="/client-portal" element={<ClientPortal />} />
        <Route path="/client-portal/projects/:id" element={<ClientProject />} />
        <Route path="/pricing" element={<PricingPage />} />
        <Route path="/billing/success" element={<BillingResult />} />
        <Route path="/billing/cancel" element={<BillingResult cancel />} />
        <Route path="/settings/profile" element={<ProfilePage />} />
        <Route path="/settings" element={<SettingsHome />} />
        <Route path="/settings/preferences" element={<PreferencesPage />} />
        <Route path="/settings/billing" element={<BillingPage />} />
        <Route path="/settings/notifications" element={<NotificationSettings />} />
        <Route path="/help" element={<HelpPage />} />
      </Route>

      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  );
}
