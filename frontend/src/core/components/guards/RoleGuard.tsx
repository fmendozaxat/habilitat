import { Navigate } from 'react-router-dom';
import { ROUTES } from '@/core/config/constants';
import { useAuthStore } from '@/auth/hooks/useAuthStore';
import type { UserRole } from '@/core/types';

interface RoleGuardProps {
  children: React.ReactNode;
  allowedRoles: UserRole[];
}

export function RoleGuard({ children, allowedRoles }: RoleGuardProps) {
  const { user } = useAuthStore();

  if (!user || !allowedRoles.includes(user.role)) {
    return <Navigate to={ROUTES.DASHBOARD} replace />;
  }

  return <>{children}</>;
}
