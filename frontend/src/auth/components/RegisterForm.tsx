import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Link } from 'react-router-dom';
import { ROUTES } from '@/core/config/constants';
import { Button, Input, Label } from '@/core/components/ui';
import { useRegister } from '../hooks';
import type { RegisterFormData } from '../types';

const registerSchema = z.object({
  firstName: z.string().min(2, 'El nombre debe tener al menos 2 caracteres'),
  lastName: z.string().min(2, 'El apellido debe tener al menos 2 caracteres'),
  email: z.string().email('Correo electrónico inválido'),
  password: z.string().min(8, 'La contraseña debe tener al menos 8 caracteres'),
  confirmPassword: z.string(),
  tenantSlug: z.string().optional(),
}).refine((data) => data.password === data.confirmPassword, {
  message: 'Las contraseñas no coinciden',
  path: ['confirmPassword'],
});

export function RegisterForm() {
  const { mutate: register, isPending } = useRegister();

  const {
    register: registerField,
    handleSubmit,
    formState: { errors },
  } = useForm<RegisterFormData>({
    resolver: zodResolver(registerSchema),
  });

  const onSubmit = (data: RegisterFormData) => {
    register({
      email: data.email,
      password: data.password,
      first_name: data.firstName,
      last_name: data.lastName,
      tenant_slug: data.tenantSlug,
    });
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <div className="row g-3 mb-3">
        <div className="col-md-6">
          <Label htmlFor="firstName">Nombre</Label>
          <Input
            id="firstName"
            placeholder="Juan"
            {...registerField('firstName')}
            error={errors.firstName?.message}
          />
        </div>

        <div className="col-md-6">
          <Label htmlFor="lastName">Apellido</Label>
          <Input
            id="lastName"
            placeholder="Pérez"
            {...registerField('lastName')}
            error={errors.lastName?.message}
          />
        </div>
      </div>

      <div className="mb-3">
        <Label htmlFor="email">Correo electrónico</Label>
        <Input
          id="email"
          type="email"
          placeholder="tu@email.com"
          {...registerField('email')}
          error={errors.email?.message}
        />
      </div>

      <div className="mb-3">
        <Label htmlFor="password">Contraseña</Label>
        <Input
          id="password"
          type="password"
          placeholder="••••••••"
          {...registerField('password')}
          error={errors.password?.message}
        />
      </div>

      <div className="mb-3">
        <Label htmlFor="confirmPassword">Confirmar contraseña</Label>
        <Input
          id="confirmPassword"
          type="password"
          placeholder="••••••••"
          {...registerField('confirmPassword')}
          error={errors.confirmPassword?.message}
        />
      </div>

      <Button type="submit" className="w-100" isLoading={isPending}>
        Crear cuenta
      </Button>

      <p className="text-center small text-muted mt-3">
        ¿Ya tienes una cuenta?{' '}
        <Link to={ROUTES.LOGIN} className="text-primary">
          Inicia sesión
        </Link>
      </p>
    </form>
  );
}
