import { ProgressBar } from 'react-bootstrap';
import { cn } from '@/core/utils';

interface ProgressProps {
  value: number;
  max?: number;
  size?: 'sm' | 'md' | 'lg';
  showLabel?: boolean;
  className?: string;
  variant?: 'primary' | 'success' | 'warning' | 'danger' | 'info';
}

const sizeStyles = {
  sm: { height: '4px' },
  md: { height: '8px' },
  lg: { height: '12px' },
};

export function Progress({
  value,
  max = 100,
  size = 'md',
  showLabel = false,
  className,
  variant = 'primary',
}: ProgressProps) {
  const percentage = Math.min(Math.max((value / max) * 100, 0), 100);

  return (
    <div className={cn('w-100', className)}>
      <ProgressBar
        now={percentage}
        variant={variant}
        style={sizeStyles[size]}
      />
      {showLabel && (
        <p className="text-end small text-muted mt-1 mb-0">
          {percentage.toFixed(0)}%
        </p>
      )}
    </div>
  );
}
