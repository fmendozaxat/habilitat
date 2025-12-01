import { RegisterForm } from '../components';

export function RegisterPage() {
  return (
    <div>
      <div className="text-center mb-4">
        <h1 className="fs-2 fw-bold">Crear Cuenta</h1>
        <p className="text-muted mt-2">
          Completa el formulario para registrarte
        </p>
      </div>
      <RegisterForm />
    </div>
  );
}
