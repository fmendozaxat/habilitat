import { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ArrowLeft, CheckCircle, Circle, Lock } from 'lucide-react';
import { Button, ProgressBar } from 'react-bootstrap';
import { LoadingPage, EmptyState } from '@/core/components/ui';
import { ROUTES } from '@/core/config/constants';
import { cn, formatPercentage } from '@/core/utils';
import { useMyAssignment, useModuleProgress, useCompleteModule } from '../hooks';
import { ModuleRenderer } from '../components';

export function AssignmentPage() {
  const { id } = useParams<{ id: string }>();
  const assignmentId = Number(id);

  const { data: assignment, isLoading: assignmentLoading } = useMyAssignment(assignmentId);
  const { data: progress, isLoading: progressLoading } = useModuleProgress(assignmentId);
  const { mutate: completeModule, isPending: isCompleting } = useCompleteModule();

  const [selectedModuleIndex, setSelectedModuleIndex] = useState(0);

  if (assignmentLoading || progressLoading) {
    return <LoadingPage />;
  }

  if (!assignment || !assignment.flow) {
    return (
      <EmptyState
        title="Asignación no encontrada"
        description="La asignación que buscas no existe"
        action={{
          label: 'Volver',
          onClick: () => window.history.back(),
        }}
      />
    );
  }

  const modules = assignment.flow.modules?.sort((a, b) => a.order_index - b.order_index) || [];
  const currentModule = modules[selectedModuleIndex];

  const getModuleProgress = (moduleId: number) => {
    return progress?.find((p) => p.module_id === moduleId);
  };

  const isModuleLocked = (index: number) => {
    if (index === 0) return false;
    const previousModule = modules[index - 1];
    const previousProgress = getModuleProgress(previousModule.id);
    return previousProgress?.status !== 'completed';
  };

  const handleCompleteModule = () => {
    if (currentModule) {
      completeModule(
        { assignmentId, moduleId: currentModule.id },
        {
          onSuccess: () => {
            if (selectedModuleIndex < modules.length - 1) {
              setSelectedModuleIndex(selectedModuleIndex + 1);
            }
          },
        }
      );
    }
  };

  return (
    <div className="min-vh-100 bg-light bg-opacity-10">
      {/* Header */}
      <div className="bg-white border-bottom sticky-top" style={{ zIndex: 10 }}>
        <div className="container py-3">
          <div className="d-flex align-items-center gap-3">
            <Link to={ROUTES.MY_ONBOARDING}>
              <Button variant="ghost" size="sm" className="p-2">
                <ArrowLeft className="h-4 w-4" />
              </Button>
            </Link>
            <div className="flex-grow-1">
              <h1 className="fw-semibold h6 mb-1">{assignment.flow.name}</h1>
              <div className="d-flex align-items-center gap-2">
                <ProgressBar
                  now={assignment.progress_percentage}
                  style={{ height: '6px', flex: '1', maxWidth: '20rem' }}
                />
                <span className="small text-muted">
                  {formatPercentage(assignment.progress_percentage)}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="container py-4">
        <div className="d-flex gap-4">
          {/* Sidebar - Module List */}
          <div className="d-none d-lg-block" style={{ width: '20rem', flexShrink: 0 }}>
            <div className="bg-white rounded border p-3 sticky-top" style={{ top: '6rem' }}>
              <h2 className="fw-semibold h6 mb-3">Contenido</h2>
              <div className="d-flex flex-column gap-2">
                {modules.map((module, index) => {
                  const moduleProgress = getModuleProgress(module.id);
                  const isCompleted = moduleProgress?.status === 'completed';
                  const locked = isModuleLocked(index);
                  const isActive = selectedModuleIndex === index;

                  return (
                    <button
                      key={module.id}
                      onClick={() => !locked && setSelectedModuleIndex(index)}
                      disabled={locked}
                      className={cn(
                        'd-flex align-items-center gap-3 w-100 p-3 rounded text-start border-0 transition',
                        isActive && 'bg-primary bg-opacity-10',
                        !isActive && !locked && 'bg-white hover-bg-light',
                        locked && 'opacity-50'
                      )}
                      style={{ cursor: locked ? 'not-allowed' : 'pointer' }}
                    >
                      {isCompleted ? (
                        <CheckCircle className="h-5 w-5 text-success flex-shrink-0" />
                      ) : locked ? (
                        <Lock className="h-5 w-5 text-muted flex-shrink-0" />
                      ) : (
                        <Circle className="h-5 w-5 text-muted flex-shrink-0" />
                      )}
                      <span
                        className={cn(
                          'small',
                          isActive && 'fw-medium',
                          isCompleted && 'text-muted'
                        )}
                      >
                        {module.title}
                      </span>
                    </button>
                  );
                })}
              </div>
            </div>
          </div>

          {/* Main Content */}
          <div className="flex-grow-1">
            {currentModule && (
              <ModuleRenderer
                module={currentModule}
                progress={getModuleProgress(currentModule.id)}
                onComplete={handleCompleteModule}
                isCompleting={isCompleting}
              />
            )}

            {/* Navigation */}
            <div className="d-flex justify-content-between mt-4">
              <Button
                variant="outline-secondary"
                onClick={() => setSelectedModuleIndex(selectedModuleIndex - 1)}
                disabled={selectedModuleIndex === 0}
              >
                Anterior
              </Button>
              <Button
                variant="primary"
                onClick={() => setSelectedModuleIndex(selectedModuleIndex + 1)}
                disabled={
                  selectedModuleIndex === modules.length - 1 ||
                  isModuleLocked(selectedModuleIndex + 1)
                }
              >
                Siguiente
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
