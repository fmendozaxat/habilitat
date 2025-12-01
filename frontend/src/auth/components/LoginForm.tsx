import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Link } from 'react-router-dom';
import { Form } from 'react-bootstrap';
import { ROUTES } from '@/core/config/constants';
import { Button } from '@/core/components/ui';
import { useLogin } from '../hooks';
import type { LoginFormData } from '../types';

const loginSchema = z.object({
  email: z.string().email('Correo electrónico inválido'),
  password: z.string().min(1, 'La contraseña es requerida'),
});

export function LoginForm() {
  const { mutate: login, isPending } = useLogin();

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
  });

  const onSubmit = (data: LoginFormData) => {
    login(data);
  };

  return (
    <Form onSubmit={handleSubmit(onSubmit)}>
      <Form.Group className="mb-3">
        <Form.Label>Correo electrónico</Form.Label>
        <Form.Control
          type="email"
          placeholder="tu@email.com"
          {...register('email')}
          isInvalid={!!errors.email}
        />
        <Form.Control.Feedback type="invalid">
          {errors.email?.message}
        </Form.Control.Feedback>
      </Form.Group>

      <Form.Group className="mb-3">
        <div className="d-flex justify-content-between align-items-center">
          <Form.Label className="mb-0">Contraseña</Form.Label>
          <Link to={ROUTES.FORGOT_PASSWORD} className="small text-primary text-decoration-none">
            ¿Olvidaste tu contraseña?
          </Link>
        </div>
        <Form.Control
          type="password"
          placeholder="••••••••"
          {...register('password')}
          isInvalid={!!errors.password}
        />
        <Form.Control.Feedback type="invalid">
          {errors.password?.message}
        </Form.Control.Feedback>
      </Form.Group>

      <Button type="submit" className="w-100 mb-3" isLoading={isPending}>
        Iniciar Sesión
      </Button>

      <p className="text-center text-muted small mb-0">
        ¿No tienes una cuenta?{' '}
        <Link to={ROUTES.REGISTER} className="text-primary text-decoration-none">
          Regístrate
        </Link>
      </p>
    </Form>
  );
}
