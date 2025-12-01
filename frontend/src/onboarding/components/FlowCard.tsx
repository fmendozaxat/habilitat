import { Link } from 'react-router-dom';
import { MoreHorizontal, Users, Clock, Edit, Trash2, Copy } from 'lucide-react';
import { useState } from 'react';
import { Card, Badge, Button, Dropdown } from 'react-bootstrap';
import { ConfirmModal } from '@/core/components/ui';
import { ROUTES } from '@/core/config/constants';
import { formatDate } from '@/core/utils';
import { useDeleteFlow } from '../hooks';
import type { OnboardingFlow } from '@/core/types';

interface FlowCardProps {
  flow: OnboardingFlow;
  onDuplicate?: (id: number) => void;
}

export function FlowCard({ flow, onDuplicate }: FlowCardProps) {
  const [showDeleteModal, setShowDeleteModal] = useState(false);

  const { mutate: deleteFlow, isPending: isDeleting } = useDeleteFlow();

  const handleDelete = () => {
    deleteFlow(flow.id, {
      onSuccess: () => setShowDeleteModal(false),
    });
  };

  const moduleCount = flow.modules?.length || 0;

  return (
    <>
      <Card className="h-100 shadow-sm" style={{ transition: 'box-shadow 0.2s' }} onMouseEnter={(e) => e.currentTarget.classList.add('shadow')} onMouseLeave={(e) => e.currentTarget.classList.remove('shadow')}>
        <Card.Body className="p-4">
          <div className="d-flex align-items-start justify-content-between">
            <div className="flex-grow-1">
              <div className="d-flex align-items-center gap-2 mb-2">
                <h3 className="fw-semibold h5 mb-0">{flow.name}</h3>
                {flow.is_default && (
                  <Badge bg="secondary">Por defecto</Badge>
                )}
                <Badge bg={flow.is_active ? 'success' : 'secondary'}>
                  {flow.is_active ? 'Activo' : 'Inactivo'}
                </Badge>
              </div>
              {flow.description && (
                <p className="small text-muted mb-3">
                  {flow.description}
                </p>
              )}
              <div className="d-flex align-items-center gap-3 small text-muted">
                <span className="d-flex align-items-center gap-1">
                  <Users className="h-4 w-4" />
                  {moduleCount} módulos
                </span>
                <span className="d-flex align-items-center gap-1">
                  <Clock className="h-4 w-4" />
                  {formatDate(flow.created_at)}
                </span>
              </div>
            </div>

            <Dropdown align="end">
              <Dropdown.Toggle variant="ghost" size="sm" className="p-2" bsPrefix="btn">
                <MoreHorizontal className="h-4 w-4" />
              </Dropdown.Toggle>

              <Dropdown.Menu>
                <Dropdown.Item as={Link} to={ROUTES.ONBOARDING_FLOW(flow.id)}>
                  <Edit className="h-4 w-4 me-2" />
                  Editar
                </Dropdown.Item>
                {onDuplicate && (
                  <Dropdown.Item onClick={() => onDuplicate(flow.id)}>
                    <Copy className="h-4 w-4 me-2" />
                    Duplicar
                  </Dropdown.Item>
                )}
                <Dropdown.Divider />
                <Dropdown.Item
                  className="text-danger"
                  onClick={() => setShowDeleteModal(true)}
                >
                  <Trash2 className="h-4 w-4 me-2" />
                  Eliminar
                </Dropdown.Item>
              </Dropdown.Menu>
            </Dropdown>
          </div>

          <div className="mt-3 pt-3 border-top">
            <Link to={ROUTES.ONBOARDING_FLOW(flow.id)} className="text-decoration-none">
              <Button variant="outline-secondary" className="w-100">
                Administrar Flujo
              </Button>
            </Link>
          </div>
        </Card.Body>
      </Card>

      <ConfirmModal
        isOpen={showDeleteModal}
        onClose={() => setShowDeleteModal(false)}
        onConfirm={handleDelete}
        title="Eliminar Flujo"
        description={`¿Estás seguro de que deseas eliminar "${flow.name}"? Esta acción no se puede deshacer.`}
        confirmText="Eliminar"
        variant="destructive"
        isLoading={isDeleting}
      />
    </>
  );
}
