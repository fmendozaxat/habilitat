import { useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ROUTES, USER_ROLES } from '@/core/config/constants';
import { ToastProvider } from '@/core/components/ui/Toast';
import { AuthGuard, GuestGuard, RoleGuard } from '@/core/components/guards';
import { MainLayout, AuthLayout } from '@/core/components/layout';
import { useAuthStore } from '@/auth/hooks/useAuthStore';

// Auth Pages
import { LoginPage, RegisterPage, ForgotPasswordPage, ResetPasswordPage } from '@/auth/pages';

// Dashboard
import { DashboardPage } from '@/dashboard/pages';

// Users
import { UsersPage } from '@/users/pages';

// Onboarding
import { FlowsPage, FlowDetailPage, MyOnboardingPage, AssignmentPage } from '@/onboarding/pages';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
      retry: 1,
    },
  },
});

function AppRoutes() {
  const { initialize, isLoading } = useAuthStore();

  useEffect(() => {
    initialize();
  }, [initialize]);

  if (isLoading) {
    return (
      <div className="d-flex vh-100 align-items-center justify-content-center">
        <div className="spinner-border text-primary" role="status">
          <span className="visually-hidden">Cargando...</span>
        </div>
      </div>
    );
  }

  return (
    <Routes>
      {/* Public Routes */}
      <Route
        element={
          <GuestGuard>
            <AuthLayout />
          </GuestGuard>
        }
      >
        <Route path={ROUTES.LOGIN} element={<LoginPage />} />
        <Route path={ROUTES.REGISTER} element={<RegisterPage />} />
        <Route path={ROUTES.FORGOT_PASSWORD} element={<ForgotPasswordPage />} />
        <Route path={ROUTES.RESET_PASSWORD} element={<ResetPasswordPage />} />
      </Route>

      {/* Protected Routes */}
      <Route
        element={
          <AuthGuard>
            <MainLayout />
          </AuthGuard>
        }
      >
        <Route path={ROUTES.DASHBOARD} element={<DashboardPage />} />

        {/* Users - Admin only */}
        <Route
          path={ROUTES.USERS}
          element={
            <RoleGuard allowedRoles={[USER_ROLES.TENANT_ADMIN, USER_ROLES.SUPER_ADMIN]}>
              <UsersPage />
            </RoleGuard>
          }
        />

        {/* Onboarding Flows - Admin only */}
        <Route
          path={ROUTES.ONBOARDING_FLOWS}
          element={
            <RoleGuard allowedRoles={[USER_ROLES.TENANT_ADMIN, USER_ROLES.SUPER_ADMIN]}>
              <FlowsPage />
            </RoleGuard>
          }
        />
        <Route
          path="/onboarding/flows/:id"
          element={
            <RoleGuard allowedRoles={[USER_ROLES.TENANT_ADMIN, USER_ROLES.SUPER_ADMIN]}>
              <FlowDetailPage />
            </RoleGuard>
          }
        />

        {/* My Onboarding - Employees */}
        <Route path={ROUTES.MY_ONBOARDING} element={<MyOnboardingPage />} />
      </Route>

      {/* Assignment Page - Full screen */}
      <Route
        path="/onboarding/assignments/:id"
        element={
          <AuthGuard>
            <AssignmentPage />
          </AuthGuard>
        }
      />

      {/* Redirects */}
      <Route path={ROUTES.HOME} element={<Navigate to={ROUTES.DASHBOARD} replace />} />
      <Route path="*" element={<Navigate to={ROUTES.DASHBOARD} replace />} />
    </Routes>
  );
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ToastProvider>
        <BrowserRouter>
          <AppRoutes />
        </BrowserRouter>
      </ToastProvider>
    </QueryClientProvider>
  );
}
