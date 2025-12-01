import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Link } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';
import { ROUTES } from '@/core/config/constants';
import { Button, Input, Label } from '@/core/components/ui';
import { useForgotPassword } from '../hooks';
import type { ForgotPasswordFormData } from '../types';

const forgotPasswordSchema = z.object({
  email: z.string().email('Correo electrónico inválido'),
});

export function ForgotPasswordForm() {
  const { mutate: forgotPassword, isPending, isSuccess } = useForgotPassword();

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ForgotPasswordFormData>({
    resolver: zodResolver(forgotPasswordSchema),
  });

  const onSubmit = (data: ForgotPasswordFormData) => {
    forgotPassword(data.email);
  };

  if (isSuccess) {
    return (
      <div className="text-center">
        <h2 className="fs-2 fw-bold mb-4">Revisa tu correo</h2>
        <p className="text-muted mb-4">
          Si el correo existe en nuestro sistema, recibirás un enlace para restablecer tu contraseña.
        </p>
        <Link
          to={ROUTES.LOGIN}
          className="d-inline-flex align-items-center gap-2 text-primary"
        >
          <ArrowLeft className="h-4 w-4" />
          Volver al inicio de sesión
        </Link>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <div className="text-center mb-4">
        <h2 className="fs-2 fw-bold">¿Olvidaste tu contraseña?</h2>
        <p className="text-muted mt-2">
          Ingresa tu correo electrónico y te enviaremos instrucciones para restablecerla.
        </p>
      </div>

      <div className="mb-3">
        <Label htmlFor="email">Correo electrónico</Label>
        <Input
          id="email"
          type="email"
          placeholder="tu@email.com"
          {...register('email')}
          error={errors.email?.message}
        />
      </div>

      <Button type="submit" className="w-100" isLoading={isPending}>
        Enviar instrucciones
      </Button>

      <p className="text-center mt-3">
        <Link
          to={ROUTES.LOGIN}
          className="d-inline-flex align-items-center gap-2 small text-primary"
        >
          <ArrowLeft className="h-4 w-4" />
          Volver al inicio de sesión
        </Link>
      </p>
    </form>
  );
}
