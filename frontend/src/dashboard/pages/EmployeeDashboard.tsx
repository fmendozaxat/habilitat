import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { GraduationCap, Clock, CheckCircle } from 'lucide-react';
import { Card, Row, Col, Badge, ProgressBar, Button } from 'react-bootstrap';
import { LoadingPage } from '@/core/components/ui';
import { ROUTES } from '@/core/config/constants';
import { formatDate, formatPercentage } from '@/core/utils';
import { useAuthStore } from '@/auth/hooks/useAuthStore';
import { api } from '@/core/api';
import type { OnboardingAssignment } from '@/core/types';

export function EmployeeDashboard() {
  const { user } = useAuthStore();

  const { data: assignments, isLoading } = useQuery({
    queryKey: ['my-assignments'],
    queryFn: () => api.get<OnboardingAssignment[]>('/onboarding/my-assignments'),
  });

  if (isLoading) {
    return <LoadingPage />;
  }

  const activeAssignment = assignments?.find((a) => a.status !== 'completed');
  const completedCount = assignments?.filter((a) => a.status === 'completed').length || 0;

  return (
    <div className="mb-4">
      <div className="mb-4">
        <h1 className="fs-2 fw-bold">
          Bienvenido, {user?.first_name}
        </h1>
        <p className="text-muted">
          Tu progreso de onboarding
        </p>
      </div>

      {/* Quick Stats */}
      <Row className="g-4 mb-4">
        <Col md={4}>
          <Card>
            <Card.Body className="p-4">
              <div className="d-flex align-items-center gap-3">
                <div className="rounded-circle bg-primary bg-opacity-10 p-3">
                  <GraduationCap className="text-primary" size={24} />
                </div>
                <div>
                  <p className="small text-muted mb-1">Asignaciones</p>
                  <p className="fs-2 fw-bold mb-0">{assignments?.length || 0}</p>
                </div>
              </div>
            </Card.Body>
          </Card>
        </Col>

        <Col md={4}>
          <Card>
            <Card.Body className="p-4">
              <div className="d-flex align-items-center gap-3">
                <div className="rounded-circle bg-success bg-opacity-10 p-3">
                  <CheckCircle className="text-success" size={24} />
                </div>
                <div>
                  <p className="small text-muted mb-1">Completados</p>
                  <p className="fs-2 fw-bold mb-0">{completedCount}</p>
                </div>
              </div>
            </Card.Body>
          </Card>
        </Col>

        <Col md={4}>
          <Card>
            <Card.Body className="p-4">
              <div className="d-flex align-items-center gap-3">
                <div className="rounded-circle bg-warning bg-opacity-10 p-3">
                  <Clock className="text-warning" size={24} />
                </div>
                <div>
                  <p className="small text-muted mb-1">En Progreso</p>
                  <p className="fs-2 fw-bold mb-0">
                    {(assignments?.length || 0) - completedCount}
                  </p>
                </div>
              </div>
            </Card.Body>
          </Card>
        </Col>
      </Row>

      {/* Active Assignment */}
      {activeAssignment && (
        <Card className="mb-4">
          <Card.Header>
            <Card.Title>Continuar Onboarding</Card.Title>
          </Card.Header>
          <Card.Body>
            <div className="d-flex flex-column flex-md-row align-items-md-center justify-content-md-between gap-3">
              <div className="flex-grow-1">
                <h3 className="fw-semibold fs-5">
                  {activeAssignment.flow?.name}
                </h3>
                <p className="small text-muted mt-1">
                  {activeAssignment.flow?.description}
                </p>
                <div className="mt-3">
                  <div className="d-flex align-items-center justify-content-between small mb-2">
                    <span>Progreso</span>
                    <span className="fw-medium">
                      {formatPercentage(activeAssignment.progress_percentage)}
                    </span>
                  </div>
                  <ProgressBar
                    now={activeAssignment.progress_percentage}
                    variant="primary"
                  />
                </div>
                {activeAssignment.due_date && (
                  <p className="small text-muted mt-2">
                    Fecha límite: {formatDate(activeAssignment.due_date)}
                  </p>
                )}
              </div>
              <Link to={ROUTES.ONBOARDING_ASSIGNMENT(activeAssignment.id)}>
                <Button variant="primary">Continuar</Button>
              </Link>
            </div>
          </Card.Body>
        </Card>
      )}

      {/* All Assignments */}
      <Card>
        <Card.Header>
          <Card.Title>Todas las Asignaciones</Card.Title>
        </Card.Header>
        <Card.Body>
          {!assignments || assignments.length === 0 ? (
            <p className="text-center text-muted py-5">
              No tienes asignaciones de onboarding
            </p>
          ) : (
            <div className="d-flex flex-column gap-3">
              {assignments.map((assignment) => (
                <div
                  key={assignment.id}
                  className="d-flex align-items-center justify-content-between p-3 rounded border"
                >
                  <div className="d-flex align-items-center gap-3">
                    <div className="rounded-circle bg-primary bg-opacity-10 p-2">
                      <GraduationCap className="text-primary" size={20} />
                    </div>
                    <div>
                      <p className="fw-medium mb-0">{assignment.flow?.name}</p>
                      <p className="small text-muted mb-0">
                        {formatPercentage(assignment.progress_percentage)} completado
                      </p>
                    </div>
                  </div>
                  <div className="d-flex align-items-center gap-3">
                    <Badge
                      bg={
                        assignment.status === 'completed'
                          ? 'success'
                          : assignment.status === 'in_progress'
                          ? 'primary'
                          : 'secondary'
                      }
                    >
                      {assignment.status === 'completed'
                        ? 'Completado'
                        : assignment.status === 'in_progress'
                        ? 'En Progreso'
                        : 'Sin Iniciar'}
                    </Badge>
                    {assignment.status !== 'completed' && (
                      <Link to={ROUTES.ONBOARDING_ASSIGNMENT(assignment.id)}>
                        <Button size="sm" variant="outline-primary">
                          {assignment.status === 'not_started' ? 'Iniciar' : 'Continuar'}
                        </Button>
                      </Link>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </Card.Body>
      </Card>
    </div>
  );
}
