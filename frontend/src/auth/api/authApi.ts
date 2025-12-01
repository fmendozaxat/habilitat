import { api } from '@/core/api';
import type { AuthTokens, User, Tenant } from '@/core/types';

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  first_name: string;
  last_name: string;
  tenant_slug?: string;
}

export interface LoginResponse extends AuthTokens {
  user: User;
  tenant: Tenant;
}

export interface RefreshRequest {
  refresh_token: string;
}

export interface ForgotPasswordRequest {
  email: string;
}

export interface ResetPasswordRequest {
  token: string;
  new_password: string;
}

export interface AcceptInvitationRequest {
  token: string;
  password: string;
  first_name: string;
  last_name: string;
}

export const authApi = {
  login: (data: LoginRequest) =>
    api.post<LoginResponse>('/auth/login', data),

  register: (data: RegisterRequest) =>
    api.post<LoginResponse>('/auth/register', data),

  logout: () =>
    api.post('/auth/logout'),

  refreshToken: (data: RefreshRequest) =>
    api.post<AuthTokens>('/auth/refresh', data),

  forgotPassword: (data: ForgotPasswordRequest) =>
    api.post('/auth/forgot-password', data),

  resetPassword: (data: ResetPasswordRequest) =>
    api.post('/auth/reset-password', data),

  verifyEmail: (token: string) =>
    api.post('/auth/verify-email', { token }),

  acceptInvitation: (data: AcceptInvitationRequest) =>
    api.post<LoginResponse>('/auth/accept-invitation', data),

  getMe: () =>
    api.get<User>('/auth/me'),

  updateProfile: (data: Partial<User>) =>
    api.patch<User>('/auth/me', data),

  changePassword: (currentPassword: string, newPassword: string) =>
    api.post('/auth/change-password', {
      current_password: currentPassword,
      new_password: newPassword,
    }),
};
