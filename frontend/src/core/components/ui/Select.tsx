import { forwardRef, type SelectHTMLAttributes } from 'react';
import { cn } from '@/core/utils';
import type { SelectOption } from '@/core/types';

export interface SelectProps extends Omit<SelectHTMLAttributes<HTMLSelectElement>, 'size'> {
  options: SelectOption[];
  placeholder?: string;
  error?: string;
  label?: string;
  selectSize?: 'sm' | 'lg';
}

const Select = forwardRef<HTMLSelectElement, SelectProps>(
  ({ className, options, placeholder, error, label, id, selectSize, ...props }, ref) => {
    const selectId = id || props.name;
    const sizeClass = selectSize ? `form-select-${selectSize}` : '';

    return (
      <div className="mb-3">
        {label && <label htmlFor={selectId} className="form-label">{label}</label>}
        <select
          id={selectId}
          className={cn('form-select', sizeClass, error && 'is-invalid', className)}
          ref={ref}
          {...props}
        >
          {placeholder && (
            <option value="" disabled>
              {placeholder}
            </option>
          )}
          {options.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
        {error && <div className="invalid-feedback">{error}</div>}
      </div>
    );
  }
);
Select.displayName = 'Select';

export { Select };
