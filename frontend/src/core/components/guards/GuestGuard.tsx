import { Navigate, useLocation } from 'react-router-dom';
import { ROUTES } from '@/core/config/constants';
import { useAuthStore } from '@/auth/hooks/useAuthStore';
import { LoadingPage } from '../ui/Spinner';

interface GuestGuardProps {
  children: React.ReactNode;
}

export function GuestGuard({ children }: GuestGuardProps) {
  const location = useLocation();
  const { isAuthenticated, isLoading } = useAuthStore();

  if (isLoading) {
    return <LoadingPage />;
  }

  if (isAuthenticated) {
    const from = location.state?.from?.pathname || ROUTES.DASHBOARD;
    return <Navigate to={from} replace />;
  }

  return <>{children}</>;
}
