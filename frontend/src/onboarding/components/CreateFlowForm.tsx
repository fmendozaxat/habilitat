import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Button, Form } from 'react-bootstrap';
import { Modal } from '@/core/components/ui';
import { useCreateFlow } from '../hooks';
import type { CreateFlowData } from '../types';

const flowSchema = z.object({
  name: z.string().min(3, 'El nombre debe tener al menos 3 caracteres'),
  description: z.string().optional(),
});

interface CreateFlowFormProps {
  isOpen: boolean;
  onClose: () => void;
}

export function CreateFlowForm({ isOpen, onClose }: CreateFlowFormProps) {
  const { mutate: createFlow, isPending } = useCreateFlow();

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<CreateFlowData>({
    resolver: zodResolver(flowSchema),
  });

  const onSubmit = (data: CreateFlowData) => {
    createFlow(data, {
      onSuccess: () => {
        reset();
        onClose();
      },
    });
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Crear Flujo de Onboarding"
      description="Crea un nuevo flujo de onboarding para tus empleados."
    >
      <Form onSubmit={handleSubmit(onSubmit)}>
        <div className="d-flex flex-column gap-3">
          <Form.Group>
            <Form.Label htmlFor="name">Nombre del flujo</Form.Label>
            <Form.Control
              id="name"
              type="text"
              placeholder="Ej: Onboarding Nuevo Empleado"
              {...register('name')}
              isInvalid={!!errors.name}
            />
            {errors.name && (
              <Form.Control.Feedback type="invalid">
                {errors.name.message}
              </Form.Control.Feedback>
            )}
          </Form.Group>

          <Form.Group>
            <Form.Label htmlFor="description">Descripción (opcional)</Form.Label>
            <Form.Control
              as="textarea"
              id="description"
              rows={3}
              placeholder="Describe el propósito de este flujo..."
              {...register('description')}
              isInvalid={!!errors.description}
            />
            {errors.description && (
              <Form.Control.Feedback type="invalid">
                {errors.description.message}
              </Form.Control.Feedback>
            )}
          </Form.Group>

          <div className="d-flex justify-content-end gap-2 pt-3">
            <Button type="button" variant="outline-secondary" onClick={onClose}>
              Cancelar
            </Button>
            <Button type="submit" variant="primary" disabled={isPending}>
              {isPending ? 'Creando...' : 'Crear Flujo'}
            </Button>
          </div>
        </div>
      </Form>
    </Modal>
  );
}
