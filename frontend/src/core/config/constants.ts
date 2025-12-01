/**
 * Application constants and configuration
 */

export const API_BASE_URL = import.meta.env.VITE_API_URL || '/api/v1';

export const APP_NAME = 'Habilitat';

export const STORAGE_KEYS = {
  ACCESS_TOKEN: 'habilitat_access_token',
  REFRESH_TOKEN: 'habilitat_refresh_token',
  USER: 'habilitat_user',
  TENANT: 'habilitat_tenant',
  THEME: 'habilitat_theme',
} as const;

export const ROUTES = {
  // Public
  HOME: '/',
  LOGIN: '/login',
  REGISTER: '/register',
  FORGOT_PASSWORD: '/forgot-password',
  RESET_PASSWORD: '/reset-password',
  ACCEPT_INVITATION: '/accept-invitation',
  VERIFY_EMAIL: '/verify-email',

  // Protected
  DASHBOARD: '/dashboard',
  PROFILE: '/profile',

  // Admin
  USERS: '/users',
  USERS_INVITE: '/users/invite',
  SETTINGS: '/settings',
  SETTINGS_BRANDING: '/settings/branding',

  // Onboarding
  MY_ONBOARDING: '/my-onboarding',
  ONBOARDING_FLOWS: '/onboarding/flows',
  ONBOARDING_FLOW: (id: number | string) => `/onboarding/flows/${id}`,
  ONBOARDING_ASSIGNMENT: (id: number | string) => `/onboarding/assignments/${id}`,

  // Content
  CONTENT: '/content',
  CONTENT_NEW: '/content/new',
  CONTENT_EDIT: (id: number | string) => `/content/${id}/edit`,

  // Analytics
  ANALYTICS: '/analytics',
} as const;

export const USER_ROLES = {
  SUPER_ADMIN: 'super_admin',
  TENANT_ADMIN: 'tenant_admin',
  EMPLOYEE: 'employee',
} as const;

export const ONBOARDING_STATUS = {
  NOT_STARTED: 'not_started',
  IN_PROGRESS: 'in_progress',
  COMPLETED: 'completed',
} as const;

export const MODULE_TYPES = {
  TEXT: 'text',
  VIDEO: 'video',
  DOCUMENT: 'document',
  QUIZ: 'quiz',
  LINK: 'link',
} as const;

export const PAGINATION = {
  DEFAULT_PAGE_SIZE: 20,
  MAX_PAGE_SIZE: 100,
} as const;
