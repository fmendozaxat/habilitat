import { Link } from 'react-router-dom';
import { GraduationCap, CheckCircle, Clock, AlertCircle } from 'lucide-react';
import { Card, Badge, ProgressBar, Button } from 'react-bootstrap';
import { LoadingPage, EmptyState } from '@/core/components/ui';
import { ROUTES } from '@/core/config/constants';
import { formatDate, formatPercentage } from '@/core/utils';
import { useMyAssignments } from '../hooks';

export function MyOnboardingPage() {
  const { data: assignments, isLoading } = useMyAssignments();

  if (isLoading) {
    return <LoadingPage />;
  }

  if (!assignments || assignments.length === 0) {
    return (
      <div className="d-flex flex-column gap-4">
        <h1 className="h2 fw-bold">Mi Onboarding</h1>
        <EmptyState
          icon={<GraduationCap className="h-8 w-8 text-muted" />}
          title="No tienes asignaciones de onboarding"
          description="Cuando se te asigne un flujo de onboarding, aparecerá aquí"
        />
      </div>
    );
  }

  const getStatusBadge = (status: string, dueDate?: string) => {
    const isOverdue = dueDate && new Date(dueDate) < new Date() && status !== 'completed';

    if (isOverdue) {
      return <Badge bg="danger">Vencido</Badge>;
    }

    switch (status) {
      case 'completed':
        return <Badge bg="success">Completado</Badge>;
      case 'in_progress':
        return <Badge bg="primary">En Progreso</Badge>;
      default:
        return <Badge bg="secondary">Sin Iniciar</Badge>;
    }
  };

  const getStatusIcon = (status: string, dueDate?: string) => {
    const isOverdue = dueDate && new Date(dueDate) < new Date() && status !== 'completed';

    if (isOverdue) {
      return <AlertCircle className="h-6 w-6 text-danger" />;
    }

    switch (status) {
      case 'completed':
        return <CheckCircle className="h-6 w-6 text-success" />;
      case 'in_progress':
        return <Clock className="h-6 w-6 text-primary" />;
      default:
        return <GraduationCap className="h-6 w-6 text-secondary" />;
    }
  };

  return (
    <div className="d-flex flex-column gap-4">
      <div>
        <h1 className="h2 fw-bold">Mi Onboarding</h1>
        <p className="text-muted">
          Completa tus flujos de onboarding asignados
        </p>
      </div>

      <div className="d-flex flex-column gap-3">
        {assignments.map((assignment) => (
          <Card key={assignment.id}>
            <Card.Body className="p-4">
              <div className="d-flex align-items-start gap-3">
                <div className="rounded-circle bg-light p-3">
                  {getStatusIcon(assignment.status, assignment.due_date)}
                </div>

                <div className="flex-grow-1">
                  <div className="d-flex align-items-center gap-2 mb-2">
                    <h3 className="fw-semibold h5 mb-0">
                      {assignment.flow?.name}
                    </h3>
                    {getStatusBadge(assignment.status, assignment.due_date)}
                  </div>

                  {assignment.flow?.description && (
                    <p className="small text-muted mb-3">
                      {assignment.flow.description}
                    </p>
                  )}

                  <div className="mb-3">
                    <div className="d-flex align-items-center justify-content-between small mb-2">
                      <span>Progreso</span>
                      <span className="fw-medium">
                        {formatPercentage(assignment.progress_percentage)}
                      </span>
                    </div>
                    <ProgressBar
                      now={assignment.progress_percentage}
                      style={{ height: '8px' }}
                    />
                  </div>

                  <div className="d-flex align-items-center justify-content-between">
                    <div className="d-flex align-items-center gap-3 small text-muted">
                      <span>Asignado: {formatDate(assignment.assigned_at)}</span>
                      {assignment.due_date && (
                        <span>Fecha límite: {formatDate(assignment.due_date)}</span>
                      )}
                    </div>

                    {assignment.status !== 'completed' && (
                      <Link to={ROUTES.ONBOARDING_ASSIGNMENT(assignment.id)}>
                        <Button variant="primary">
                          {assignment.status === 'not_started' ? 'Iniciar' : 'Continuar'}
                        </Button>
                      </Link>
                    )}
                  </div>
                </div>
              </div>
            </Card.Body>
          </Card>
        ))}
      </div>
    </div>
  );
}
