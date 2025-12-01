import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useToast } from '@/core/components/ui/Toast';
import { usersApi } from '../api/usersApi';
import type { UserFilters, CreateUserData, UpdateUserData, InviteUserData } from '../types';

export function useUsers(filters?: UserFilters) {
  return useQuery({
    queryKey: ['users', filters],
    queryFn: () => usersApi.getUsers(filters),
  });
}

export function useUser(id: number) {
  return useQuery({
    queryKey: ['users', id],
    queryFn: () => usersApi.getUser(id),
    enabled: !!id,
  });
}

export function useCreateUser() {
  const queryClient = useQueryClient();
  const { success, error } = useToast();

  return useMutation({
    mutationFn: (data: CreateUserData) => usersApi.createUser(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] });
      success('Usuario creado', 'El usuario ha sido creado exitosamente');
    },
    onError: (err: Error) => {
      error('Error', err.message);
    },
  });
}

export function useUpdateUser() {
  const queryClient = useQueryClient();
  const { success, error } = useToast();

  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: UpdateUserData }) =>
      usersApi.updateUser(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] });
      success('Usuario actualizado', 'El usuario ha sido actualizado exitosamente');
    },
    onError: (err: Error) => {
      error('Error', err.message);
    },
  });
}

export function useDeleteUser() {
  const queryClient = useQueryClient();
  const { success, error } = useToast();

  return useMutation({
    mutationFn: (id: number) => usersApi.deleteUser(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] });
      success('Usuario eliminado', 'El usuario ha sido eliminado exitosamente');
    },
    onError: (err: Error) => {
      error('Error', err.message);
    },
  });
}

export function useInviteUser() {
  const queryClient = useQueryClient();
  const { success, error } = useToast();

  return useMutation({
    mutationFn: (data: InviteUserData) => usersApi.inviteUser(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] });
      success('Invitación enviada', 'Se ha enviado la invitación al correo electrónico');
    },
    onError: (err: Error) => {
      error('Error', err.message);
    },
  });
}

export function useToggleUserActive() {
  const queryClient = useQueryClient();
  const { success, error } = useToast();

  return useMutation({
    mutationFn: (id: number) => usersApi.toggleActive(id),
    onSuccess: (user) => {
      queryClient.invalidateQueries({ queryKey: ['users'] });
      success(
        user.is_active ? 'Usuario activado' : 'Usuario desactivado',
        `El usuario ha sido ${user.is_active ? 'activado' : 'desactivado'}`
      );
    },
    onError: (err: Error) => {
      error('Error', err.message);
    },
  });
}
