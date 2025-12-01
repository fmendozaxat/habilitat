import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts';
import { Card } from 'react-bootstrap';
import type { OnboardingAnalytics } from '@/core/types';

interface OnboardingChartProps {
  analytics: OnboardingAnalytics;
}

const COLORS = ['#22c55e', '#3b82f6', '#94a3b8', '#ef4444'];

export function OnboardingChart({ analytics }: OnboardingChartProps) {
  const data = [
    { name: 'Completados', value: analytics.completed },
    { name: 'En Progreso', value: analytics.in_progress },
    { name: 'Sin Iniciar', value: analytics.not_started },
    { name: 'Vencidos', value: analytics.overdue },
  ].filter((item) => item.value > 0);

  if (analytics.total_assignments === 0) {
    return (
      <Card>
        <Card.Header>
          <Card.Title>Estado de Onboarding</Card.Title>
        </Card.Header>
        <Card.Body style={{ height: '300px' }} className="d-flex align-items-center justify-content-center">
          <p className="text-muted">No hay asignaciones de onboarding</p>
        </Card.Body>
      </Card>
    );
  }

  return (
    <Card>
      <Card.Header>
        <Card.Title>Estado de Onboarding</Card.Title>
      </Card.Header>
      <Card.Body>
        <div style={{ height: '300px' }}>
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={data}
                cx="50%"
                cy="50%"
                innerRadius={60}
                outerRadius={100}
                paddingAngle={2}
                dataKey="value"
              >
                {data.map((_, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip
                formatter={(value: number) => [value, 'Asignaciones']}
                contentStyle={{
                  backgroundColor: 'white',
                  border: '1px solid #e2e8f0',
                  borderRadius: '8px',
                }}
              />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </div>
        <div className="mt-3 text-center">
          <p className="small text-muted mb-0">
            Total: {analytics.total_assignments} asignaciones
          </p>
        </div>
      </Card.Body>
    </Card>
  );
}
