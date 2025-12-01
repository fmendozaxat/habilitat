import { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ArrowLeft, Plus, GripVertical, Edit, Trash2 } from 'lucide-react';
import { Card, Button, Badge } from 'react-bootstrap';
import { LoadingPage, EmptyState, ConfirmModal } from '@/core/components/ui';
import { ROUTES } from '@/core/config/constants';
import { useFlow, useModules, useDeleteModule } from '../hooks';
import type { OnboardingModule } from '@/core/types';

const moduleTypeLabels = {
  text: 'Texto',
  video: 'Video',
  document: 'Documento',
  quiz: 'Quiz',
  link: 'Enlace',
};

export function FlowDetailPage() {
  const { id } = useParams<{ id: string }>();
  const flowId = Number(id);

  const { data: flow, isLoading: flowLoading } = useFlow(flowId);
  const { data: modules, isLoading: modulesLoading } = useModules(flowId);

  const [moduleToDelete, setModuleToDelete] = useState<OnboardingModule | null>(null);
  const { mutate: deleteModule, isPending: isDeleting } = useDeleteModule();

  const handleDeleteModule = () => {
    if (moduleToDelete) {
      deleteModule(moduleToDelete.id, {
        onSuccess: () => setModuleToDelete(null),
      });
    }
  };

  if (flowLoading || modulesLoading) {
    return <LoadingPage />;
  }

  if (!flow) {
    return (
      <EmptyState
        title="Flujo no encontrado"
        description="El flujo que buscas no existe"
        action={{
          label: 'Volver a flujos',
          onClick: () => window.history.back(),
        }}
      />
    );
  }

  return (
    <div className="d-flex flex-column gap-4">
      {/* Header */}
      <div className="d-flex align-items-center gap-3">
        <Link to={ROUTES.ONBOARDING_FLOWS}>
          <Button variant="ghost" size="sm" className="p-2">
            <ArrowLeft className="h-4 w-4" />
          </Button>
        </Link>
        <div className="flex-grow-1">
          <div className="d-flex align-items-center gap-2">
            <h1 className="h2 fw-bold mb-0">{flow.name}</h1>
            <Badge bg={flow.is_active ? 'success' : 'secondary'}>
              {flow.is_active ? 'Activo' : 'Inactivo'}
            </Badge>
          </div>
          {flow.description && (
            <p className="text-muted mb-0">{flow.description}</p>
          )}
        </div>
        <Button variant="outline-secondary">
          <Edit className="h-4 w-4 me-2" />
          Editar
        </Button>
      </div>

      {/* Modules */}
      <Card>
        <Card.Header className="d-flex align-items-center justify-content-between">
          <Card.Title as="h5" className="mb-0">Módulos del Flujo</Card.Title>
          <Button variant="primary" size="sm">
            <Plus className="h-4 w-4 me-2" />
            Agregar Módulo
          </Button>
        </Card.Header>
        <Card.Body>
          {!modules || modules.length === 0 ? (
            <EmptyState
              title="No hay módulos"
              description="Agrega módulos a este flujo para comenzar"
            />
          ) : (
            <div className="d-flex flex-column gap-3">
              {modules
                .sort((a, b) => a.order_index - b.order_index)
                .map((module, index) => (
                  <div
                    key={module.id}
                    className="d-flex align-items-center gap-3 p-3 rounded border bg-white"
                    style={{ transition: 'background-color 0.2s' }}
                    onMouseEnter={(e) => e.currentTarget.classList.add('bg-light')}
                    onMouseLeave={(e) => e.currentTarget.classList.remove('bg-light')}
                  >
                    <div className="text-muted" style={{ cursor: 'grab' }}>
                      <GripVertical className="h-5 w-5" />
                    </div>
                    <div className="d-flex align-items-center justify-content-center rounded-circle bg-primary bg-opacity-10 text-primary fw-medium small" style={{ width: '2rem', height: '2rem' }}>
                      {index + 1}
                    </div>
                    <div className="flex-grow-1">
                      <div className="d-flex align-items-center gap-2">
                        <p className="fw-medium mb-0">{module.title}</p>
                        <Badge bg="light" text="dark" className="border">
                          {moduleTypeLabels[module.module_type]}
                        </Badge>
                        {module.is_required && (
                          <Badge bg="secondary">Requerido</Badge>
                        )}
                      </div>
                      {module.description && (
                        <p className="small text-muted mb-0 mt-1">
                          {module.description}
                        </p>
                      )}
                    </div>
                    <div className="d-flex align-items-center gap-2">
                      <Button variant="ghost" size="sm" className="p-2">
                        <Edit className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="p-2"
                        onClick={() => setModuleToDelete(module)}
                      >
                        <Trash2 className="h-4 w-4 text-danger" />
                      </Button>
                    </div>
                  </div>
                ))}
            </div>
          )}
        </Card.Body>
      </Card>

      <ConfirmModal
        isOpen={!!moduleToDelete}
        onClose={() => setModuleToDelete(null)}
        onConfirm={handleDeleteModule}
        title="Eliminar Módulo"
        description={`¿Estás seguro de que deseas eliminar "${moduleToDelete?.title}"?`}
        confirmText="Eliminar"
        variant="destructive"
        isLoading={isDeleting}
      />
    </div>
  );
}
