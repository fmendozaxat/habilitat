import { create } from 'zustand';
import { storage } from '@/core/utils/storage';
import { authApi, type LoginRequest, type RegisterRequest } from '../api/authApi';
import type { User, Tenant, AuthTokens } from '@/core/types';

interface AuthState {
  user: User | null;
  tenant: Tenant | null;
  tokens: AuthTokens | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
}

interface AuthActions {
  login: (credentials: LoginRequest) => Promise<void>;
  register: (data: RegisterRequest) => Promise<void>;
  logout: () => void;
  initialize: () => Promise<void>;
  updateUser: (user: Partial<User>) => void;
  clearError: () => void;
}

type AuthStore = AuthState & AuthActions;

export const useAuthStore = create<AuthStore>((set, get) => ({
  user: null,
  tenant: null,
  tokens: null,
  isAuthenticated: false,
  isLoading: true,
  error: null,

  login: async (credentials: LoginRequest) => {
    try {
      set({ isLoading: true, error: null });
      const response = await authApi.login(credentials);

      const tokens: AuthTokens = {
        access_token: response.access_token,
        refresh_token: response.refresh_token,
        token_type: response.token_type,
      };

      storage.setTokens(tokens);
      storage.setUser(response.user);
      storage.setTenant(response.tenant);

      set({
        user: response.user,
        tenant: response.tenant,
        tokens,
        isAuthenticated: true,
        isLoading: false,
      });
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : 'Error al iniciar sesión',
        isLoading: false,
      });
      throw error;
    }
  },

  register: async (data: RegisterRequest) => {
    try {
      set({ isLoading: true, error: null });
      const response = await authApi.register(data);

      const tokens: AuthTokens = {
        access_token: response.access_token,
        refresh_token: response.refresh_token,
        token_type: response.token_type,
      };

      storage.setTokens(tokens);
      storage.setUser(response.user);
      storage.setTenant(response.tenant);

      set({
        user: response.user,
        tenant: response.tenant,
        tokens,
        isAuthenticated: true,
        isLoading: false,
      });
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : 'Error al registrarse',
        isLoading: false,
      });
      throw error;
    }
  },

  logout: () => {
    storage.clearAll();
    set({
      user: null,
      tenant: null,
      tokens: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,
    });
  },

  initialize: async () => {
    const accessToken = storage.getAccessToken();

    if (!accessToken) {
      set({ isLoading: false });
      return;
    }

    try {
      const user = await authApi.getMe();
      const storedTenant = storage.getTenant();

      set({
        user,
        tenant: storedTenant,
        isAuthenticated: true,
        isLoading: false,
      });
    } catch {
      storage.clearAll();
      set({
        user: null,
        tenant: null,
        tokens: null,
        isAuthenticated: false,
        isLoading: false,
      });
    }
  },

  updateUser: (userData: Partial<User>) => {
    const currentUser = get().user;
    if (currentUser) {
      const updatedUser = { ...currentUser, ...userData };
      storage.setUser(updatedUser);
      set({ user: updatedUser });
    }
  },

  clearError: () => set({ error: null }),
}));
