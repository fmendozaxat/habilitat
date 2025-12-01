import { type ReactNode } from 'react';
import { Modal as BsModal } from 'react-bootstrap';
import { Button } from './Button';

interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  description?: string;
  children: ReactNode;
  size?: 'sm' | 'lg' | 'xl';
  showClose?: boolean;
}

export function Modal({
  isOpen,
  onClose,
  title,
  description,
  children,
  size,
  showClose = true,
}: ModalProps) {
  return (
    <BsModal show={isOpen} onHide={onClose} size={size} centered>
      {(title || showClose) && (
        <BsModal.Header closeButton={showClose}>
          {title && <BsModal.Title>{title}</BsModal.Title>}
          {description && <p className="text-muted mb-0 small">{description}</p>}
        </BsModal.Header>
      )}
      <BsModal.Body>{children}</BsModal.Body>
    </BsModal>
  );
}

interface ConfirmModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  title: string;
  description: string;
  confirmText?: string;
  cancelText?: string;
  variant?: 'primary' | 'danger' | 'destructive';
  isLoading?: boolean;
}

export function ConfirmModal({
  isOpen,
  onClose,
  onConfirm,
  title,
  description,
  confirmText = 'Confirmar',
  cancelText = 'Cancelar',
  variant = 'primary',
  isLoading = false,
}: ConfirmModalProps) {
  const buttonVariant = variant === 'destructive' ? 'danger' : variant;

  return (
    <BsModal show={isOpen} onHide={onClose} centered size="sm">
      <BsModal.Header>
        <BsModal.Title>{title}</BsModal.Title>
      </BsModal.Header>
      <BsModal.Body>
        <p className="text-muted">{description}</p>
      </BsModal.Body>
      <BsModal.Footer>
        <Button variant="secondary" onClick={onClose} disabled={isLoading}>
          {cancelText}
        </Button>
        <Button
          variant={buttonVariant}
          onClick={onConfirm}
          isLoading={isLoading}
        >
          {confirmText}
        </Button>
      </BsModal.Footer>
    </BsModal>
  );
}
