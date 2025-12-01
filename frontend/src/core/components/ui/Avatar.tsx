import { cn } from '@/core/utils';
import { getInitials } from '@/core/utils/format';

interface AvatarProps {
  src?: string | null;
  firstName: string;
  lastName?: string;
  size?: 'sm' | 'md' | 'lg' | 'xl';
  className?: string;
}

const sizeStyles = {
  sm: { width: '32px', height: '32px', fontSize: '0.75rem' },
  md: { width: '40px', height: '40px', fontSize: '0.875rem' },
  lg: { width: '48px', height: '48px', fontSize: '1rem' },
  xl: { width: '64px', height: '64px', fontSize: '1.25rem' },
};

export function Avatar({ src, firstName, lastName, size = 'md', className }: AvatarProps) {
  const initials = getInitials(firstName, lastName);

  if (src) {
    return (
      <img
        src={src}
        alt={`${firstName} ${lastName || ''}`}
        className={cn('rounded-circle', className)}
        style={{ ...sizeStyles[size], objectFit: 'cover' }}
      />
    );
  }

  return (
    <div
      className={cn('rounded-circle bg-primary text-white d-flex align-items-center justify-content-center fw-medium', className)}
      style={sizeStyles[size]}
    >
      {initials}
    </div>
  );
}
