import { useState } from 'react';
import { Plus, Search } from 'lucide-react';
import { Button, Form, InputGroup, Row, Col } from 'react-bootstrap';
import { EmptyState } from '@/core/components/ui';
import { PAGINATION } from '@/core/config/constants';
import { useFlows } from '../hooks';
import { FlowCard, CreateFlowForm } from '../components';
import type { FlowFilters } from '../types';

export function FlowsPage() {
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [filters, setFilters] = useState<FlowFilters>({
    page: 1,
    page_size: PAGINATION.DEFAULT_PAGE_SIZE,
  });

  const { data, isLoading } = useFlows(filters);

  return (
    <div className="d-flex flex-column gap-4">
      <div className="d-flex align-items-center justify-content-between">
        <div>
          <h1 className="h2 fw-bold">Flujos de Onboarding</h1>
          <p className="text-muted">
            Crea y gestiona flujos de onboarding para tus empleados
          </p>
        </div>
        <Button variant="primary" onClick={() => setShowCreateModal(true)}>
          <Plus className="h-4 w-4 me-2" />
          Crear Flujo
        </Button>
      </div>

      {/* Search */}
      <div className="d-flex gap-3">
        <div className="position-relative flex-grow-1" style={{ maxWidth: '28rem' }}>
          <InputGroup>
            <InputGroup.Text className="bg-white">
              <Search className="h-4 w-4 text-muted" />
            </InputGroup.Text>
            <Form.Control
              type="text"
              placeholder="Buscar flujos..."
              value={filters.search || ''}
              onChange={(e) =>
                setFilters({ ...filters, search: e.target.value, page: 1 })
              }
            />
          </InputGroup>
        </div>
      </div>

      {/* Flows Grid */}
      {isLoading ? (
        <Row xs={1} md={2} lg={3} className="g-3">
          {[1, 2, 3].map((i) => (
            <Col key={i}>
              <div
                className="rounded border bg-light placeholder-glow"
                style={{ height: '12rem' }}
              />
            </Col>
          ))}
        </Row>
      ) : !data?.items || data.items.length === 0 ? (
        <EmptyState
          title="No hay flujos de onboarding"
          description="Crea tu primer flujo de onboarding para comenzar"
          action={{
            label: 'Crear Flujo',
            onClick: () => setShowCreateModal(true),
          }}
        />
      ) : (
        <Row xs={1} md={2} lg={3} className="g-3">
          {data.items.map((flow) => (
            <Col key={flow.id}>
              <FlowCard flow={flow} />
            </Col>
          ))}
        </Row>
      )}

      <CreateFlowForm
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
      />
    </div>
  );
}
