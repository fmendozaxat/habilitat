import { Outlet } from 'react-router-dom';
import { Container, Row, Col } from 'react-bootstrap';
import { useAuthStore } from '@/auth/hooks/useAuthStore';

export function AuthLayout() {
  const { tenant } = useAuthStore();

  return (
    <div className="auth-container">
      <Container>
        <Row className="justify-content-center">
          <Col xs={12} sm={10} md={8} lg={6} xl={5}>
            <div className="auth-card">
              <div className="text-center mb-4">
                {tenant?.branding?.logo_url ? (
                  <img
                    src={tenant.branding.logo_url}
                    alt={tenant.name}
                    style={{ height: '48px' }}
                    className="mb-3"
                  />
                ) : (
                  <h2 className="text-primary fw-bold mb-2">Habilitat</h2>
                )}
                <p className="text-muted small">Plataforma de onboarding para empresas</p>
              </div>
              <Outlet />
            </div>
          </Col>
        </Row>
      </Container>
    </div>
  );
}
