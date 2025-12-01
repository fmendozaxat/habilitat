import { Link, useNavigate } from 'react-router-dom';
import { Navbar, Nav, Dropdown, Badge } from 'react-bootstrap';
import { Menu, Bell, LogOut, User } from 'lucide-react';
import { ROUTES } from '@/core/config/constants';
import { useAuthStore } from '@/auth/hooks/useAuthStore';
import { Avatar } from '../ui/Avatar';

interface HeaderProps {
  onMenuClick: () => void;
}

export function Header({ onMenuClick }: HeaderProps) {
  const navigate = useNavigate();
  const { user, logout } = useAuthStore();

  const handleLogout = () => {
    logout();
    navigate(ROUTES.LOGIN);
  };

  return (
    <Navbar bg="white" className="border-bottom px-3 py-2" style={{ height: '64px' }}>
      {/* Left side */}
      <button
        className="btn btn-link text-dark d-lg-none p-0 me-3"
        onClick={onMenuClick}
      >
        <Menu size={24} />
      </button>

      {/* Right side */}
      <Nav className="ms-auto d-flex align-items-center gap-3">
        {/* Notifications */}
        <button className="btn btn-link text-dark position-relative p-0">
          <Bell size={20} />
          <Badge
            bg="danger"
            pill
            className="position-absolute"
            style={{ top: '-5px', right: '-5px', fontSize: '0.6rem' }}
          >
            3
          </Badge>
        </button>

        {/* User menu */}
        <Dropdown align="end">
          <Dropdown.Toggle
            as="button"
            className="btn btn-link text-dark d-flex align-items-center gap-2 p-0 text-decoration-none"
          >
            <Avatar
              src={user?.profile_image_url}
              firstName={user?.first_name || ''}
              lastName={user?.last_name}
              size="sm"
            />
            <span className="d-none d-md-inline">
              {user?.first_name} {user?.last_name}
            </span>
          </Dropdown.Toggle>

          <Dropdown.Menu>
            <Dropdown.Item as={Link} to={ROUTES.PROFILE}>
              <User size={16} className="me-2" />
              Mi Perfil
            </Dropdown.Item>
            <Dropdown.Divider />
            <Dropdown.Item onClick={handleLogout} className="text-danger">
              <LogOut size={16} className="me-2" />
              Cerrar Sesión
            </Dropdown.Item>
          </Dropdown.Menu>
        </Dropdown>
      </Nav>
    </Navbar>
  );
}
