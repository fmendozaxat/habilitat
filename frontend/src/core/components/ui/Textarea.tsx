import { forwardRef, type TextareaHTMLAttributes } from 'react';
import { cn } from '@/core/utils';

export interface TextareaProps extends TextareaHTMLAttributes<HTMLTextAreaElement> {
  error?: string;
  label?: string;
}

const Textarea = forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ className, error, label, id, ...props }, ref) => {
    const textareaId = id || props.name;

    return (
      <div className="mb-3">
        {label && <label htmlFor={textareaId} className="form-label">{label}</label>}
        <textarea
          id={textareaId}
          className={cn('form-control', error && 'is-invalid', className)}
          ref={ref}
          rows={3}
          {...props}
        />
        {error && <div className="invalid-feedback">{error}</div>}
      </div>
    );
  }
);
Textarea.displayName = 'Textarea';

export { Textarea };
