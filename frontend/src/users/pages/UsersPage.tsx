import { useState } from 'react';
import { UserPlus, Search } from 'lucide-react';
import { Card, Button, Form, Row, Col } from 'react-bootstrap';
import { USER_ROLES, PAGINATION } from '@/core/config/constants';
import { useUsers } from '../hooks';
import { UsersTable, InviteUserForm } from '../components';
import type { UserFilters } from '../types';

export function UsersPage() {
  const [showInviteModal, setShowInviteModal] = useState(false);
  const [filters, setFilters] = useState<UserFilters>({
    page: 1,
    page_size: PAGINATION.DEFAULT_PAGE_SIZE,
  });

  const { data, isLoading } = useUsers(filters);

  const roleOptions = [
    { value: '', label: 'Todos los roles' },
    { value: USER_ROLES.TENANT_ADMIN, label: 'Administrador' },
    { value: USER_ROLES.EMPLOYEE, label: 'Empleado' },
  ];

  const statusOptions = [
    { value: '', label: 'Todos los estados' },
    { value: 'true', label: 'Activos' },
    { value: 'false', label: 'Inactivos' },
  ];

  return (
    <div className="mb-4">
      <div className="d-flex align-items-center justify-content-between mb-4">
        <div>
          <h1 className="h2 fw-bold mb-2">Usuarios</h1>
          <p className="text-muted">
            Gestiona los usuarios de tu organización
          </p>
        </div>
        <Button onClick={() => setShowInviteModal(true)}>
          <UserPlus className="me-2" size={16} />
          Invitar Usuario
        </Button>
      </div>

      <Card>
        <Card.Header>
          <Card.Title>Lista de Usuarios</Card.Title>
        </Card.Header>
        <Card.Body>
          {/* Filters */}
          <Row className="g-3 mb-4">
            <Col xs={12} md={6}>
              <div className="position-relative">
                <Search className="position-absolute top-50 start-0 translate-middle-y ms-3 text-muted" size={16} />
                <Form.Control
                  type="text"
                  placeholder="Buscar por nombre o correo..."
                  className="ps-5"
                  value={filters.search || ''}
                  onChange={(e) =>
                    setFilters({ ...filters, search: e.target.value, page: 1 })
                  }
                />
              </div>
            </Col>
            <Col xs={12} md={3}>
              <Form.Select
                value={filters.role || ''}
                onChange={(e) =>
                  setFilters({
                    ...filters,
                    role: e.target.value as typeof filters.role,
                    page: 1,
                  })
                }
              >
                {roleOptions.map(option => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </Form.Select>
            </Col>
            <Col xs={12} md={3}>
              <Form.Select
                value={filters.is_active?.toString() || ''}
                onChange={(e) =>
                  setFilters({
                    ...filters,
                    is_active: e.target.value ? e.target.value === 'true' : undefined,
                    page: 1,
                  })
                }
              >
                {statusOptions.map(option => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </Form.Select>
            </Col>
          </Row>

          <UsersTable
            users={data?.data || []}
            isLoading={isLoading}
            pagination={{
              page: filters.page || 1,
              pageSize: filters.page_size || PAGINATION.DEFAULT_PAGE_SIZE,
              total: data?.total || 0,
            }}
            onPageChange={(page) => setFilters({ ...filters, page })}
          />
        </Card.Body>
      </Card>

      <InviteUserForm
        isOpen={showInviteModal}
        onClose={() => setShowInviteModal(false)}
      />
    </div>
  );
}
