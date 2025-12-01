import { forwardRef, type ButtonHTMLAttributes } from 'react';
import { Spinner } from 'react-bootstrap';
import { cn } from '@/core/utils';

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'success' | 'danger' | 'warning' | 'info' | 'light' | 'dark' | 'link' | 'outline-primary' | 'outline-secondary' | 'outline-danger' | 'ghost' | 'outline' | 'destructive';
  size?: 'sm' | 'md' | 'lg' | 'icon';
  isLoading?: boolean;
}

const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = 'primary', size = 'md', isLoading, children, disabled, ...props }, ref) => {
    // Map old variants to Bootstrap variants
    let bsVariant = variant;
    if (variant === 'ghost') bsVariant = 'light';
    if (variant === 'outline') bsVariant = 'outline-secondary';
    if (variant === 'destructive') bsVariant = 'danger';

    // Size class
    let sizeClass = '';
    if (size === 'sm') sizeClass = 'btn-sm';
    if (size === 'lg') sizeClass = 'btn-lg';
    if (size === 'icon') sizeClass = 'btn-sm p-2';

    return (
      <button
        className={cn(
          'btn',
          `btn-${bsVariant}`,
          sizeClass,
          className
        )}
        ref={ref}
        disabled={disabled || isLoading}
        {...props}
      >
        {isLoading && (
          <Spinner
            as="span"
            animation="border"
            size="sm"
            role="status"
            aria-hidden="true"
            className="me-2"
          />
        )}
        {children}
      </button>
    );
  }
);
Button.displayName = 'Button';

export { Button };
