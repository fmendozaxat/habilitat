import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useSearchParams } from 'react-router-dom';
import { Button, Input, Label } from '@/core/components/ui';
import { useResetPassword } from '../hooks';
import type { ResetPasswordFormData } from '../types';

const resetPasswordSchema = z.object({
  token: z.string(),
  password: z.string().min(8, 'La contraseña debe tener al menos 8 caracteres'),
  confirmPassword: z.string(),
}).refine((data) => data.password === data.confirmPassword, {
  message: 'Las contraseñas no coinciden',
  path: ['confirmPassword'],
});

export function ResetPasswordForm() {
  const [searchParams] = useSearchParams();
  const token = searchParams.get('token') || '';

  const { mutate: resetPassword, isPending } = useResetPassword();

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ResetPasswordFormData>({
    resolver: zodResolver(resetPasswordSchema),
    defaultValues: { token },
  });

  const onSubmit = (data: ResetPasswordFormData) => {
    resetPassword({ token: data.token, password: data.password });
  };

  if (!token) {
    return (
      <div className="text-center">
        <h2 className="fs-2 fw-bold text-danger mb-4">Enlace inválido</h2>
        <p className="text-muted">
          El enlace para restablecer la contraseña no es válido o ha expirado.
        </p>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <div className="text-center mb-4">
        <h2 className="fs-2 fw-bold">Restablecer contraseña</h2>
        <p className="text-muted mt-2">
          Ingresa tu nueva contraseña.
        </p>
      </div>

      <input type="hidden" {...register('token')} />

      <div className="mb-3">
        <Label htmlFor="password">Nueva contraseña</Label>
        <Input
          id="password"
          type="password"
          placeholder="••••••••"
          {...register('password')}
          error={errors.password?.message}
        />
      </div>

      <div className="mb-3">
        <Label htmlFor="confirmPassword">Confirmar contraseña</Label>
        <Input
          id="confirmPassword"
          type="password"
          placeholder="••••••••"
          {...register('confirmPassword')}
          error={errors.confirmPassword?.message}
        />
      </div>

      <Button type="submit" className="w-100" isLoading={isPending}>
        Restablecer contraseña
      </Button>
    </form>
  );
}
