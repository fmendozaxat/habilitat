import { STORAGE_KEYS } from '@/core/config/constants';
import type { AuthTokens, User, Tenant } from '@/core/types';

/**
 * Storage utilities for managing local storage
 */

export const storage = {
  // Token management
  getAccessToken(): string | null {
    return localStorage.getItem(STORAGE_KEYS.ACCESS_TOKEN);
  },

  setAccessToken(token: string): void {
    localStorage.setItem(STORAGE_KEYS.ACCESS_TOKEN, token);
  },

  getRefreshToken(): string | null {
    return localStorage.getItem(STORAGE_KEYS.REFRESH_TOKEN);
  },

  setRefreshToken(token: string): void {
    localStorage.setItem(STORAGE_KEYS.REFRESH_TOKEN, token);
  },

  setTokens(tokens: AuthTokens): void {
    this.setAccessToken(tokens.access_token);
    this.setRefreshToken(tokens.refresh_token);
  },

  clearTokens(): void {
    localStorage.removeItem(STORAGE_KEYS.ACCESS_TOKEN);
    localStorage.removeItem(STORAGE_KEYS.REFRESH_TOKEN);
  },

  // User management
  getUser(): User | null {
    const data = localStorage.getItem(STORAGE_KEYS.USER);
    return data ? JSON.parse(data) : null;
  },

  setUser(user: User): void {
    localStorage.setItem(STORAGE_KEYS.USER, JSON.stringify(user));
  },

  clearUser(): void {
    localStorage.removeItem(STORAGE_KEYS.USER);
  },

  // Tenant management
  getTenant(): Tenant | null {
    const data = localStorage.getItem(STORAGE_KEYS.TENANT);
    return data ? JSON.parse(data) : null;
  },

  setTenant(tenant: Tenant): void {
    localStorage.setItem(STORAGE_KEYS.TENANT, JSON.stringify(tenant));
  },

  clearTenant(): void {
    localStorage.removeItem(STORAGE_KEYS.TENANT);
  },

  // Theme management
  getTheme(): 'light' | 'dark' {
    return (localStorage.getItem(STORAGE_KEYS.THEME) as 'light' | 'dark') || 'light';
  },

  setTheme(theme: 'light' | 'dark'): void {
    localStorage.setItem(STORAGE_KEYS.THEME, theme);
  },

  // Clear all
  clearAll(): void {
    this.clearTokens();
    this.clearUser();
    this.clearTenant();
  },
};
