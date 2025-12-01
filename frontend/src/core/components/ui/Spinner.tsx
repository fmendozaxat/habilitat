import { Spinner as BsSpinner } from 'react-bootstrap';

interface SpinnerProps {
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export function Spinner({ size = 'md', className }: SpinnerProps) {
  const bsSize = size === 'lg' ? undefined : 'sm';

  return (
    <BsSpinner
      animation="border"
      role="status"
      size={bsSize}
      className={className}
      style={size === 'lg' ? { width: '2rem', height: '2rem' } : undefined}
    >
      <span className="visually-hidden">Cargando...</span>
    </BsSpinner>
  );
}

export function LoadingPage() {
  return (
    <div className="d-flex vh-100 w-100 align-items-center justify-content-center">
      <Spinner size="lg" />
    </div>
  );
}

export function LoadingOverlay() {
  return (
    <div className="loading-overlay">
      <div className="bg-white p-4 rounded">
        <Spinner size="lg" />
      </div>
    </div>
  );
}
