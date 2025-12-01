import { api } from '@/core/api';
import type { User, PaginatedResponse } from '@/core/types';
import type { CreateUserData, UpdateUserData, InviteUserData, UserFilters } from '../types';

export const usersApi = {
  getUsers: (filters?: UserFilters) =>
    api.get<PaginatedResponse<User>>('/users', filters as Record<string, unknown>),

  getUser: (id: number) =>
    api.get<User>(`/users/${id}`),

  createUser: (data: CreateUserData) =>
    api.post<User>('/users', data),

  updateUser: (id: number, data: UpdateUserData) =>
    api.patch<User>(`/users/${id}`, data),

  deleteUser: (id: number) =>
    api.delete(`/users/${id}`),

  inviteUser: (data: InviteUserData) =>
    api.post('/users/invite', data),

  resendInvitation: (userId: number) =>
    api.post(`/users/${userId}/resend-invitation`),

  toggleActive: (id: number) =>
    api.post<User>(`/users/${id}/toggle-active`),
};
