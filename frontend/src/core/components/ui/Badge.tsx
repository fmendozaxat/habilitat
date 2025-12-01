import { type HTMLAttributes } from 'react';
import { Badge as BsBadge } from 'react-bootstrap';
import { cn } from '@/core/utils';

type BadgeVariant = 'primary' | 'secondary' | 'success' | 'warning' | 'danger' | 'info' | 'light' | 'dark' | 'default' | 'destructive' | 'outline';

export interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  variant?: BadgeVariant;
  pill?: boolean;
}

function Badge({ className, variant = 'primary', pill = false, children, ...props }: BadgeProps) {
  // Map old variants to Bootstrap variants
  let bsVariant: string = variant;
  if (variant === 'default') bsVariant = 'secondary';
  if (variant === 'destructive') bsVariant = 'danger';
  if (variant === 'outline') bsVariant = 'light';

  return (
    <BsBadge
      bg={bsVariant as 'primary' | 'secondary' | 'success' | 'warning' | 'danger' | 'info' | 'light' | 'dark'}
      pill={pill}
      className={cn(variant === 'outline' && 'border', className)}
      {...props}
    >
      {children}
    </BsBadge>
  );
}

const badgeVariants = {}; // For backwards compatibility

export { Badge, badgeVariants };
