import { type ReactNode } from 'react';
import { FileQuestion } from 'lucide-react';
import { cn } from '@/core/utils';
import { Button } from './Button';

interface EmptyStateProps {
  icon?: ReactNode;
  title: string;
  description?: string;
  action?: {
    label: string;
    onClick: () => void;
  };
  className?: string;
}

export function EmptyState({
  icon,
  title,
  description,
  action,
  className,
}: EmptyStateProps) {
  return (
    <div
      className={cn(
        'd-flex flex-column align-items-center justify-content-center py-5 text-center',
        className
      )}
    >
      <div className="mb-3 rounded-circle bg-light p-4">
        {icon || <FileQuestion size={32} className="text-muted" />}
      </div>
      <h5 className="fw-semibold">{title}</h5>
      {description && (
        <p className="mt-2 text-muted" style={{ maxWidth: '24rem' }}>
          {description}
        </p>
      )}
      {action && (
        <Button className="mt-3" onClick={action.onClick}>
          {action.label}
        </Button>
      )}
    </div>
  );
}
