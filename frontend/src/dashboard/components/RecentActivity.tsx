import { CheckCircle, Clock } from 'lucide-react';
import { Card, Row, Col } from 'react-bootstrap';
import { formatRelativeTime } from '@/core/utils';

interface RecentActivityProps {
  recentCompletions: Array<{
    user_name: string;
    flow_name: string;
    completed_at: string;
  }>;
  upcomingDeadlines: Array<{
    user_name: string;
    flow_name: string;
    due_date: string;
  }>;
}

export function RecentActivity({ recentCompletions, upcomingDeadlines }: RecentActivityProps) {
  return (
    <Row className="g-4">
      <Col lg={6}>
        <Card>
          <Card.Header>
            <Card.Title className="d-flex align-items-center gap-2">
              <CheckCircle className="text-success" size={20} />
              Completados Recientemente
            </Card.Title>
          </Card.Header>
          <Card.Body>
            {recentCompletions.length === 0 ? (
              <p className="small text-muted mb-0">No hay completados recientes</p>
            ) : (
              <div className="d-flex flex-column gap-3">
                {recentCompletions.map((item, index) => (
                  <div key={index} className="d-flex align-items-start justify-content-between">
                    <div>
                      <p className="fw-medium mb-0">{item.user_name}</p>
                      <p className="small text-muted mb-0">{item.flow_name}</p>
                    </div>
                    <p className="small text-muted mb-0">
                      {formatRelativeTime(item.completed_at)}
                    </p>
                  </div>
                ))}
              </div>
            )}
          </Card.Body>
        </Card>
      </Col>

      <Col lg={6}>
        <Card>
          <Card.Header>
            <Card.Title className="d-flex align-items-center gap-2">
              <Clock className="text-warning" size={20} />
              Próximos Vencimientos
            </Card.Title>
          </Card.Header>
          <Card.Body>
            {upcomingDeadlines.length === 0 ? (
              <p className="small text-muted mb-0">No hay vencimientos próximos</p>
            ) : (
              <div className="d-flex flex-column gap-3">
                {upcomingDeadlines.map((item, index) => (
                  <div key={index} className="d-flex align-items-start justify-content-between">
                    <div>
                      <p className="fw-medium mb-0">{item.user_name}</p>
                      <p className="small text-muted mb-0">{item.flow_name}</p>
                    </div>
                    <p className="small text-warning fw-medium mb-0">
                      {formatRelativeTime(item.due_date)}
                    </p>
                  </div>
                ))}
              </div>
            )}
          </Card.Body>
        </Card>
      </Col>
    </Row>
  );
}
