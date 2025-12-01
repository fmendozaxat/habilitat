import { forwardRef, type LabelHTMLAttributes } from 'react';
import { cn } from '@/core/utils';

const Label = forwardRef<HTMLLabelElement, LabelHTMLAttributes<HTMLLabelElement>>(
  ({ className, ...props }, ref) => (
    <label
      ref={ref}
      className={cn('form-label', className)}
      {...props}
    />
  )
);
Label.displayName = 'Label';

export { Label };
