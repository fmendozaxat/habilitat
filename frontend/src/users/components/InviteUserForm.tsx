import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Modal, Button, Form } from 'react-bootstrap';
import { USER_ROLES } from '@/core/config/constants';
import { useInviteUser } from '../hooks';

type InviteFormValues = {
  email: string;
  role: 'tenant_admin' | 'employee';
};

const inviteSchema = z.object({
  email: z.string().email('Correo electrónico inválido'),
  role: z.enum(['tenant_admin', 'employee'] as const),
});

interface InviteUserFormProps {
  isOpen: boolean;
  onClose: () => void;
}

export function InviteUserForm({ isOpen, onClose }: InviteUserFormProps) {
  const { mutate: inviteUser, isPending } = useInviteUser();

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<InviteFormValues>({
    resolver: zodResolver(inviteSchema),
    defaultValues: {
      role: 'employee',
    },
  });

  const onSubmit = (data: InviteFormValues) => {
    inviteUser(data, {
      onSuccess: () => {
        reset();
        onClose();
      },
    });
  };

  const roleOptions = [
    { value: USER_ROLES.TENANT_ADMIN, label: 'Administrador' },
    { value: USER_ROLES.EMPLOYEE, label: 'Empleado' },
  ];

  return (
    <Modal show={isOpen} onHide={onClose} centered>
      <Modal.Header closeButton>
        <Modal.Title>Invitar Usuario</Modal.Title>
      </Modal.Header>
      <Modal.Body>
        <p className="text-muted mb-4">
          Envía una invitación por correo electrónico para que un nuevo usuario se una a tu organización.
        </p>
        <Form onSubmit={handleSubmit(onSubmit)}>
          <Form.Group className="mb-3">
            <Form.Label htmlFor="email">Correo electrónico</Form.Label>
            <Form.Control
              id="email"
              type="email"
              placeholder="usuario@empresa.com"
              {...register('email')}
              isInvalid={!!errors.email}
            />
            <Form.Control.Feedback type="invalid">
              {errors.email?.message}
            </Form.Control.Feedback>
          </Form.Group>

          <Form.Group className="mb-3">
            <Form.Label htmlFor="role">Rol</Form.Label>
            <Form.Select
              id="role"
              {...register('role')}
              isInvalid={!!errors.role}
            >
              {roleOptions.map(option => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </Form.Select>
            <Form.Control.Feedback type="invalid">
              {errors.role?.message}
            </Form.Control.Feedback>
          </Form.Group>

          <div className="d-flex justify-content-end gap-2 pt-3">
            <Button variant="secondary" onClick={onClose}>
              Cancelar
            </Button>
            <Button type="submit" variant="primary" disabled={isPending}>
              {isPending ? 'Enviando...' : 'Enviar Invitación'}
            </Button>
          </div>
        </Form>
      </Modal.Body>
    </Modal>
  );
}
