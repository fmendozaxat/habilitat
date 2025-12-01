import { Users, GraduationCap, CheckCircle, Clock } from 'lucide-react';
import { Card, Row, Col } from 'react-bootstrap';
import { formatPercentage } from '@/core/utils';
import type { DashboardStats } from '@/core/types';

interface StatsCardsProps {
  stats: DashboardStats;
}

export function StatsCards({ stats }: StatsCardsProps) {
  const cards = [
    {
      title: 'Usuarios Activos',
      value: stats.active_users,
      total: stats.total_users,
      icon: Users,
      color: 'text-primary',
      bgColor: 'bg-primary',
    },
    {
      title: 'Flujos Activos',
      value: stats.total_flows,
      icon: GraduationCap,
      color: 'text-secondary',
      bgColor: 'bg-secondary',
    },
    {
      title: 'Tasa de Completado',
      value: formatPercentage(stats.completion_rate),
      icon: CheckCircle,
      color: 'text-success',
      bgColor: 'bg-success',
    },
    {
      title: 'Tiempo Promedio',
      value: `${stats.average_completion_time_days} días`,
      icon: Clock,
      color: 'text-warning',
      bgColor: 'bg-warning',
    },
  ];

  return (
    <Row className="g-4">
      {cards.map((card) => (
        <Col key={card.title} md={6} lg={3}>
          <Card>
            <Card.Body className="p-4">
              <div className="d-flex align-items-center justify-content-between">
                <div>
                  <p className="small fw-medium text-muted mb-1">
                    {card.title}
                  </p>
                  <p className="fs-2 fw-bold mt-1 mb-0">{card.value}</p>
                  {card.total && (
                    <p className="small text-muted mt-1 mb-0">
                      de {card.total} totales
                    </p>
                  )}
                </div>
                <div className={`rounded-circle ${card.bgColor} bg-opacity-10 p-3`}>
                  <card.icon className={card.color} size={24} />
                </div>
              </div>
            </Card.Body>
          </Card>
        </Col>
      ))}
    </Row>
  );
}
