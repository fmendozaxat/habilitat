import { Navigate, useLocation } from 'react-router-dom';
import { ROUTES } from '@/core/config/constants';
import { useAuthStore } from '@/auth/hooks/useAuthStore';
import { LoadingPage } from '../ui/Spinner';

interface AuthGuardProps {
  children: React.ReactNode;
}

export function AuthGuard({ children }: AuthGuardProps) {
  const location = useLocation();
  const { isAuthenticated, isLoading } = useAuthStore();

  if (isLoading) {
    return <LoadingPage />;
  }

  if (!isAuthenticated) {
    return <Navigate to={ROUTES.LOGIN} state={{ from: location }} replace />;
  }

  return <>{children}</>;
}
