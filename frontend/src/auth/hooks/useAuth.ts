import { useMutation } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { ROUTES } from '@/core/config/constants';
import { useToast } from '@/core/components/ui/Toast';
import { authApi } from '../api/authApi';
import { useAuthStore } from './useAuthStore';

export function useLogin() {
  const navigate = useNavigate();
  const { login } = useAuthStore();
  const { success, error } = useToast();

  return useMutation({
    mutationFn: login,
    onSuccess: () => {
      success('Bienvenido', 'Has iniciado sesión correctamente');
      navigate(ROUTES.DASHBOARD);
    },
    onError: (err: Error) => {
      error('Error', err.message);
    },
  });
}

export function useRegister() {
  const navigate = useNavigate();
  const { register } = useAuthStore();
  const { success, error } = useToast();

  return useMutation({
    mutationFn: register,
    onSuccess: () => {
      success('Cuenta creada', 'Tu cuenta ha sido creada exitosamente');
      navigate(ROUTES.DASHBOARD);
    },
    onError: (err: Error) => {
      error('Error', err.message);
    },
  });
}

export function useForgotPassword() {
  const { success, error } = useToast();

  return useMutation({
    mutationFn: (email: string) => authApi.forgotPassword({ email }),
    onSuccess: () => {
      success(
        'Correo enviado',
        'Si el correo existe, recibirás instrucciones para restablecer tu contraseña'
      );
    },
    onError: (err: Error) => {
      error('Error', err.message);
    },
  });
}

export function useResetPassword() {
  const navigate = useNavigate();
  const { success, error } = useToast();

  return useMutation({
    mutationFn: ({ token, password }: { token: string; password: string }) =>
      authApi.resetPassword({ token, new_password: password }),
    onSuccess: () => {
      success('Contraseña actualizada', 'Ya puedes iniciar sesión con tu nueva contraseña');
      navigate(ROUTES.LOGIN);
    },
    onError: (err: Error) => {
      error('Error', err.message);
    },
  });
}

export function useAcceptInvitation() {
  const navigate = useNavigate();
  const { success, error } = useToast();

  return useMutation({
    mutationFn: authApi.acceptInvitation,
    onSuccess: () => {
      success('Invitación aceptada', 'Tu cuenta ha sido creada exitosamente');
      navigate(ROUTES.DASHBOARD);
    },
    onError: (err: Error) => {
      error('Error', err.message);
    },
  });
}

export function useChangePassword() {
  const { success, error } = useToast();

  return useMutation({
    mutationFn: ({ currentPassword, newPassword }: { currentPassword: string; newPassword: string }) =>
      authApi.changePassword(currentPassword, newPassword),
    onSuccess: () => {
      success('Contraseña actualizada', 'Tu contraseña ha sido cambiada exitosamente');
    },
    onError: (err: Error) => {
      error('Error', err.message);
    },
  });
}

export function useUpdateProfile() {
  const { updateUser } = useAuthStore();
  const { success, error } = useToast();

  return useMutation({
    mutationFn: authApi.updateProfile,
    onSuccess: (user) => {
      updateUser(user);
      success('Perfil actualizado', 'Tus datos han sido actualizados correctamente');
    },
    onError: (err: Error) => {
      error('Error', err.message);
    },
  });
}
