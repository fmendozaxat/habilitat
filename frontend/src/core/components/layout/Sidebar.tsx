import { NavLink } from 'react-router-dom';
import { Nav, Offcanvas } from 'react-bootstrap';
import {
  LayoutDashboard,
  Users,
  GraduationCap,
  FileText,
  BarChart3,
  Settings,
} from 'lucide-react';
import { cn } from '@/core/utils';
import { ROUTES, USER_ROLES } from '@/core/config/constants';
import { useAuthStore } from '@/auth/hooks/useAuthStore';

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
}

const navigation: Array<{
  name: string;
  href: string;
  icon: typeof LayoutDashboard;
  roles: string[];
}> = [
  { name: 'Dashboard', href: ROUTES.DASHBOARD, icon: LayoutDashboard, roles: ['all'] },
  { name: 'Mi Onboarding', href: ROUTES.MY_ONBOARDING, icon: GraduationCap, roles: [USER_ROLES.EMPLOYEE] },
  { name: 'Usuarios', href: ROUTES.USERS, icon: Users, roles: [USER_ROLES.TENANT_ADMIN, USER_ROLES.SUPER_ADMIN] },
  { name: 'Onboarding', href: ROUTES.ONBOARDING_FLOWS, icon: GraduationCap, roles: [USER_ROLES.TENANT_ADMIN, USER_ROLES.SUPER_ADMIN] },
  { name: 'Contenido', href: ROUTES.CONTENT, icon: FileText, roles: [USER_ROLES.TENANT_ADMIN, USER_ROLES.SUPER_ADMIN] },
  { name: 'Analytics', href: ROUTES.ANALYTICS, icon: BarChart3, roles: [USER_ROLES.TENANT_ADMIN, USER_ROLES.SUPER_ADMIN] },
  { name: 'Configuración', href: ROUTES.SETTINGS, icon: Settings, roles: [USER_ROLES.TENANT_ADMIN, USER_ROLES.SUPER_ADMIN] },
];

function SidebarContent({ onClose }: { onClose: () => void }) {
  const { user, tenant } = useAuthStore();

  const filteredNavigation = navigation.filter((item) => {
    if (item.roles.includes('all')) return true;
    return user && item.roles.includes(user.role);
  });

  return (
    <>
      <div className="p-3 border-bottom">
        <span className="h5 text-white mb-0 fw-bold">{tenant?.name || 'Habilitat'}</span>
      </div>

      <Nav className="flex-column p-2">
        {filteredNavigation.map((item) => (
          <Nav.Item key={item.name}>
            <NavLink
              to={item.href}
              onClick={onClose}
              className={({ isActive }) =>
                cn(
                  'nav-link d-flex align-items-center gap-2',
                  isActive && 'active'
                )
              }
            >
              <item.icon size={20} />
              {item.name}
            </NavLink>
          </Nav.Item>
        ))}
      </Nav>

      <div className="mt-auto p-3 border-top">
        <p className="text-center text-muted small mb-0">Powered by Habilitat</p>
      </div>
    </>
  );
}

export function Sidebar({ isOpen, onClose }: SidebarProps) {
  return (
    <>
      {/* Desktop sidebar */}
      <div className="sidebar d-none d-lg-flex flex-column">
        <SidebarContent onClose={onClose} />
      </div>

      {/* Mobile sidebar (offcanvas) */}
      <Offcanvas
        show={isOpen}
        onHide={onClose}
        className="sidebar"
        style={{ width: '250px' }}
      >
        <Offcanvas.Header closeButton closeVariant="white">
          <Offcanvas.Title className="text-white">Menu</Offcanvas.Title>
        </Offcanvas.Header>
        <Offcanvas.Body className="p-0 d-flex flex-column">
          <SidebarContent onClose={onClose} />
        </Offcanvas.Body>
      </Offcanvas>
    </>
  );
}
