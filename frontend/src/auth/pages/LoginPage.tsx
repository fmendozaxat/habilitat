import { LoginForm } from '../components';

export function LoginPage() {
  return (
    <div>
      <div className="text-center mb-4">
        <h1 className="fs-2 fw-bold">Iniciar Sesión</h1>
        <p className="text-muted mt-2">
          Ingresa tus credenciales para acceder
        </p>
      </div>
      <LoginForm />
    </div>
  );
}
