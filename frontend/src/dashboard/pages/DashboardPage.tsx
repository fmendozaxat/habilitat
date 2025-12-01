import { Container, Row, Col, Card, Alert } from 'react-bootstrap';
import { useAuthStore } from '@/auth/hooks/useAuthStore';
import { USER_ROLES } from '@/core/config/constants';
import { EmployeeDashboard } from './EmployeeDashboard';
import { Users, GraduationCap, CheckCircle, Clock } from 'lucide-react';

export function DashboardPage() {
  const { user } = useAuthStore();

  // Employees see a different dashboard
  if (user?.role === USER_ROLES.EMPLOYEE) {
    return <EmployeeDashboard />;
  }

  return <AdminDashboard />;
}

function AdminDashboard() {
  const { user, tenant } = useAuthStore();

  return (
    <Container fluid className="py-3">
      <div className="mb-4">
        <h1 className="h3 mb-1">Bienvenido, {user?.first_name}</h1>
        <p className="text-muted mb-0">
          Panel de administración de {tenant?.name || 'Habilitat'}
        </p>
      </div>

      <Alert variant="info" className="mb-4">
        <Alert.Heading className="h6 mb-1">Dashboard en construcción</Alert.Heading>
        <p className="mb-0 small">
          Los datos mostrados aquí son de ejemplo. La integración con el backend está en progreso.
        </p>
      </Alert>

      {/* Stats Cards */}
      <Row className="g-3 mb-4">
        <Col xs={12} sm={6} lg={3}>
          <Card className="stats-card h-100">
            <Card.Body className="d-flex align-items-center">
              <div className="rounded-circle bg-primary bg-opacity-10 p-3 me-3">
                <Users className="text-primary" size={24} />
              </div>
              <div>
                <p className="text-muted small mb-0">Total Usuarios</p>
                <h3 className="mb-0">12</h3>
              </div>
            </Card.Body>
          </Card>
        </Col>

        <Col xs={12} sm={6} lg={3}>
          <Card className="stats-card success h-100">
            <Card.Body className="d-flex align-items-center">
              <div className="rounded-circle bg-success bg-opacity-10 p-3 me-3">
                <GraduationCap className="text-success" size={24} />
              </div>
              <div>
                <p className="text-muted small mb-0">Flujos Activos</p>
                <h3 className="mb-0">3</h3>
              </div>
            </Card.Body>
          </Card>
        </Col>

        <Col xs={12} sm={6} lg={3}>
          <Card className="stats-card warning h-100">
            <Card.Body className="d-flex align-items-center">
              <div className="rounded-circle bg-warning bg-opacity-10 p-3 me-3">
                <Clock className="text-warning" size={24} />
              </div>
              <div>
                <p className="text-muted small mb-0">En Progreso</p>
                <h3 className="mb-0">5</h3>
              </div>
            </Card.Body>
          </Card>
        </Col>

        <Col xs={12} sm={6} lg={3}>
          <Card className="stats-card h-100" style={{ borderLeftColor: '#22c55e' }}>
            <Card.Body className="d-flex align-items-center">
              <div className="rounded-circle bg-success bg-opacity-10 p-3 me-3">
                <CheckCircle className="text-success" size={24} />
              </div>
              <div>
                <p className="text-muted small mb-0">Completados</p>
                <h3 className="mb-0">24</h3>
              </div>
            </Card.Body>
          </Card>
        </Col>
      </Row>

      {/* Main Content */}
      <Row className="g-3">
        <Col lg={8}>
          <Card>
            <Card.Header>
              <Card.Title className="mb-0">Progreso de Onboarding</Card.Title>
            </Card.Header>
            <Card.Body>
              <div className="text-center py-5 text-muted">
                <GraduationCap size={48} className="mb-3 opacity-50" />
                <p>Los gráficos de analytics estarán disponibles próximamente</p>
              </div>
            </Card.Body>
          </Card>
        </Col>

        <Col lg={4}>
          <Card>
            <Card.Header>
              <Card.Title className="mb-0">Actividad Reciente</Card.Title>
            </Card.Header>
            <Card.Body>
              <div className="d-flex flex-column gap-3">
                <div className="d-flex align-items-center">
                  <div className="rounded-circle bg-success bg-opacity-10 p-2 me-3">
                    <CheckCircle className="text-success" size={16} />
                  </div>
                  <div>
                    <p className="mb-0 small fw-medium">Juan Pérez completó módulo</p>
                    <p className="mb-0 text-muted small">Hace 2 horas</p>
                  </div>
                </div>

                <div className="d-flex align-items-center">
                  <div className="rounded-circle bg-primary bg-opacity-10 p-2 me-3">
                    <Users className="text-primary" size={16} />
                  </div>
                  <div>
                    <p className="mb-0 small fw-medium">Nuevo usuario registrado</p>
                    <p className="mb-0 text-muted small">Hace 5 horas</p>
                  </div>
                </div>

                <div className="d-flex align-items-center">
                  <div className="rounded-circle bg-warning bg-opacity-10 p-2 me-3">
                    <Clock className="text-warning" size={16} />
                  </div>
                  <div>
                    <p className="mb-0 small fw-medium">María inició onboarding</p>
                    <p className="mb-0 text-muted small">Ayer</p>
                  </div>
                </div>
              </div>
            </Card.Body>
          </Card>
        </Col>
      </Row>
    </Container>
  );
}
