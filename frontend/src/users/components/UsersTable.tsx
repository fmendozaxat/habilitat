import { useState } from 'react';
import { MoreHorizontal, Power, Trash2 } from 'lucide-react';
import { Table, Badge, Button, Dropdown, Modal } from 'react-bootstrap';
import { formatDate, formatFullName } from '@/core/utils';
import { useDeleteUser, useToggleUserActive } from '../hooks';
import type { User, PaginationConfig } from '@/core/types';

interface UsersTableProps {
  users: User[];
  isLoading: boolean;
  pagination: PaginationConfig;
  onPageChange: (page: number) => void;
}

const roleLabels: Record<string, string> = {
  super_admin: 'Super Admin',
  tenant_admin: 'Admin',
  employee: 'Empleado',
};

export function UsersTable({ users, isLoading, pagination, onPageChange }: UsersTableProps) {
  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  const [showDeleteModal, setShowDeleteModal] = useState(false);

  const { mutate: deleteUser, isPending: isDeleting } = useDeleteUser();
  const { mutate: toggleActive } = useToggleUserActive();

  const handleDelete = () => {
    if (selectedUser) {
      deleteUser(selectedUser.id, {
        onSuccess: () => {
          setShowDeleteModal(false);
          setSelectedUser(null);
        },
      });
    }
  };

  const renderUserCell = (user: User) => (
    <div className="d-flex align-items-center gap-3">
      <div className="d-flex align-items-center justify-content-center rounded-circle bg-primary text-white"
           style={{ width: '40px', height: '40px' }}>
        {user.profile_image_url ? (
          <img src={user.profile_image_url} alt="" className="rounded-circle" style={{ width: '40px', height: '40px', objectFit: 'cover' }} />
        ) : (
          <span className="fw-medium">
            {user.first_name?.[0]}{user.last_name?.[0]}
          </span>
        )}
      </div>
      <div>
        <p className="mb-0 fw-medium">{formatFullName(user.first_name, user.last_name)}</p>
        <small className="text-muted">{user.email}</small>
      </div>
    </div>
  );

  const renderRoleCell = (user: User) => (
    <Badge bg="secondary">{roleLabels[user.role] || user.role}</Badge>
  );

  const renderStatusCell = (user: User) => (
    <Badge bg={user.is_active ? 'success' : 'danger'}>
      {user.is_active ? 'Activo' : 'Inactivo'}
    </Badge>
  );

  const renderActionsCell = (user: User) => (
    <Dropdown align="end">
      <Dropdown.Toggle variant="ghost" size="sm" className="border-0 bg-transparent">
        <MoreHorizontal size={16} />
      </Dropdown.Toggle>

      <Dropdown.Menu>
        <Dropdown.Item
          onClick={() => toggleActive(user.id)}
          className="d-flex align-items-center gap-2"
        >
          <Power size={16} />
          {user.is_active ? 'Desactivar' : 'Activar'}
        </Dropdown.Item>
        <Dropdown.Divider />
        <Dropdown.Item
          onClick={() => {
            setSelectedUser(user);
            setShowDeleteModal(true);
          }}
          className="d-flex align-items-center gap-2 text-danger"
        >
          <Trash2 size={16} />
          Eliminar
        </Dropdown.Item>
      </Dropdown.Menu>
    </Dropdown>
  );

  if (isLoading) {
    return (
      <div className="text-center py-5">
        <div className="spinner-border text-primary" role="status">
          <span className="visually-hidden">Cargando...</span>
        </div>
      </div>
    );
  }

  if (users.length === 0) {
    return (
      <div className="text-center py-5 text-muted">
        No hay usuarios
      </div>
    );
  }

  return (
    <>
      <div className="table-responsive">
        <Table hover className="align-middle">
          <thead>
            <tr>
              <th>Usuario</th>
              <th>Rol</th>
              <th>Estado</th>
              <th>Fecha de Registro</th>
              <th className="text-end">Acciones</th>
            </tr>
          </thead>
          <tbody>
            {users.map((user) => (
              <tr key={user.id}>
                <td>{renderUserCell(user)}</td>
                <td>{renderRoleCell(user)}</td>
                <td>{renderStatusCell(user)}</td>
                <td>{formatDate(user.created_at)}</td>
                <td className="text-end">{renderActionsCell(user)}</td>
              </tr>
            ))}
          </tbody>
        </Table>
      </div>

      {/* Pagination */}
      {pagination.total > pagination.pageSize && (
        <nav aria-label="Navegación de páginas" className="mt-4">
          <ul className="pagination justify-content-center mb-0">
            <li className={`page-item ${pagination.page === 1 ? 'disabled' : ''}`}>
              <button
                className="page-link"
                onClick={() => onPageChange(pagination.page - 1)}
                disabled={pagination.page === 1}
              >
                Anterior
              </button>
            </li>
            {Array.from(
              { length: Math.ceil(pagination.total / pagination.pageSize) },
              (_, i) => i + 1
            ).map((page) => (
              <li key={page} className={`page-item ${pagination.page === page ? 'active' : ''}`}>
                <button
                  className="page-link"
                  onClick={() => onPageChange(page)}
                >
                  {page}
                </button>
              </li>
            ))}
            <li className={`page-item ${pagination.page === Math.ceil(pagination.total / pagination.pageSize) ? 'disabled' : ''}`}>
              <button
                className="page-link"
                onClick={() => onPageChange(pagination.page + 1)}
                disabled={pagination.page === Math.ceil(pagination.total / pagination.pageSize)}
              >
                Siguiente
              </button>
            </li>
          </ul>
        </nav>
      )}

      {/* Delete Confirmation Modal */}
      <Modal show={showDeleteModal} onHide={() => setShowDeleteModal(false)} centered>
        <Modal.Header closeButton>
          <Modal.Title>Eliminar Usuario</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          ¿Estás seguro de que deseas eliminar a {selectedUser?.first_name} {selectedUser?.last_name}? Esta acción no se puede deshacer.
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowDeleteModal(false)}>
            Cancelar
          </Button>
          <Button variant="danger" onClick={handleDelete} disabled={isDeleting}>
            {isDeleting ? 'Eliminando...' : 'Eliminar'}
          </Button>
        </Modal.Footer>
      </Modal>
    </>
  );
}
