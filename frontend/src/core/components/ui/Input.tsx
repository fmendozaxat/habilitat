import { forwardRef, type InputHTMLAttributes } from 'react';
import { cn } from '@/core/utils';

export interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  error?: string;
  label?: string;
}

const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ className, type, error, label, id, ...props }, ref) => {
    const inputId = id || props.name;

    return (
      <div className="mb-3">
        {label && (
          <label htmlFor={inputId} className="form-label">
            {label}
          </label>
        )}
        <input
          type={type}
          id={inputId}
          className={cn(
            'form-control',
            error && 'is-invalid',
            className
          )}
          ref={ref}
          {...props}
        />
        {error && <div className="invalid-feedback">{error}</div>}
      </div>
    );
  }
);
Input.displayName = 'Input';

export { Input };
