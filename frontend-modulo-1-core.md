# Frontend Módulo 1: Core (Infraestructura Base)

## Descripción

El módulo Core es la base del frontend. Contiene toda la infraestructura compartida: cliente HTTP, layouts, theming dinámico, componentes UI base, contexts globales, y utilidades comunes.

**Límite de líneas:** ~4000-5000 líneas total

## Responsabilidades

1. Cliente HTTP (Axios) con interceptors
2. Sistema de theming dinámico (Tailwind + CSS vars)
3. Layouts principales (RootLayout, AuthLayout)
4. Componentes UI compartidos (shadcn/ui)
5. Auth context y guards
6. Error boundaries
7. Utilidades globales
8. TypeScript types globales

## Estructura de Archivos

```
src/core/
├── api/
│   ├── client.ts              # Axios client configurado
│   ├── interceptors.ts        # Request/response interceptors
│   └── index.ts
├── components/
│   ├── layouts/
│   │   ├── RootLayout.tsx     # Layout principal con sidebar
│   │   ├── AuthLayout.tsx     # Layout para auth pages
│   │   ├── Navbar.tsx
│   │   ├── Sidebar.tsx
│   │   └── Footer.tsx
│   ├── guards/
│   │   ├── ProtectedRoute.tsx  # Requiere auth
│   │   ├── AdminRoute.tsx      # Requiere admin role
│   │   └── GuestRoute.tsx      # Solo no autenticados
│   ├── ui/                     # shadcn/ui components
│   │   ├── button.tsx
│   │   ├── input.tsx
│   │   ├── card.tsx
│   │   ├── dialog.tsx
│   │   ├── dropdown-menu.tsx
│   │   ├── form.tsx
│   │   ├── table.tsx
│   │   ├── toast.tsx
│   │   └── ...más componentes
│   ├── common/
│   │   ├── LoadingSpinner.tsx
│   │   ├── ErrorBoundary.tsx
│   │   ├── PageHeader.tsx
│   │   ├── EmptyState.tsx
│   │   ├── ConfirmDialog.tsx
│   │   └── Avatar.tsx
│   └── index.ts
├── config/
│   ├── constants.ts           # Constantes globales
│   ├── env.ts                 # Environment variables con validación
│   └── routes.ts              # Rutas de la app
├── contexts/
│   ├── ThemeContext.tsx       # Tenant theming
│   └── index.ts
├── hooks/
│   ├── useAuth.ts             # Hook de autenticación
│   ├── useTenant.ts           # Hook del tenant actual
│   ├── useDebounce.ts
│   ├── useLocalStorage.ts
│   ├── useMediaQuery.ts
│   └── index.ts
├── theme/
│   ├── theme.ts               # Aplicar colores del tenant
│   ├── colors.ts              # Paleta de colores
│   └── index.ts
├── types/
│   ├── api.types.ts           # Response types de API
│   ├── auth.types.ts
│   ├── common.types.ts
│   └── index.ts
├── utils/
│   ├── format.ts              # Formateo de fechas, números, etc.
│   ├── validation.ts          # Validaciones comunes
│   ├── storage.ts             # LocalStorage helpers
│   └── index.ts
└── index.ts
```

## 1. API Client (api/client.ts)

### Axios Client con Interceptors

```typescript
import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios';
import { env } from '@/core/config/env';

export const apiClient = axios.create({
  baseURL: env.API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000, // 30 segundos
});

// Request interceptor: Add auth token and tenant ID
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    // Auth token
    const token = localStorage.getItem('auth_token');
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    // Tenant ID (desde subdomain o header)
    const tenantId = getTenantId();
    if (tenantId && config.headers) {
      config.headers['X-Tenant-ID'] = tenantId;
    }

    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor: Handle errors globally
apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      // Unauthorized - redirect to login
      localStorage.removeItem('auth_token');
      localStorage.removeItem('auth_user');
      window.location.href = '/login';
    }

    if (error.response?.status === 403) {
      // Forbidden
      // Mostrar toast de error
    }

    if (error.response?.status === 500) {
      // Server error
      // Mostrar toast de error
    }

    return Promise.reject(error);
  }
);

// Helper para obtener tenant ID
function getTenantId(): string | null {
  // Desde subdomain
  const subdomain = window.location.hostname.split('.')[0];
  if (subdomain && subdomain !== 'app' && subdomain !== 'localhost') {
    return subdomain;
  }

  // Desde localStorage (fallback para desarrollo)
  return localStorage.getItem('tenant_id');
}
```

## 2. Layouts (components/layouts/)

### RootLayout.tsx

```typescript
import { Outlet, useNavigate } from 'react-router-dom';
import { Navbar } from './Navbar';
import { Sidebar } from './Sidebar';
import { useAuth } from '@/core/hooks/useAuth';
import { useTenant } from '@/core/hooks/useTenant';
import { useEffect } from 'react';
import { applyTenantTheme } from '@/core/theme/theme';

export function RootLayout() {
  const { user } = useAuth();
  const { tenant } = useTenant();
  const navigate = useNavigate();

  // Aplicar theming del tenant
  useEffect(() => {
    if (tenant?.branding) {
      applyTenantTheme(tenant.branding);
    }
  }, [tenant]);

  // Redirect si no está autenticado
  useEffect(() => {
    if (!user) {
      navigate('/login');
    }
  }, [user, navigate]);

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Sidebar */}
      <Sidebar />

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        <Navbar />

        <main className="flex-1 overflow-y-auto p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
```

### Navbar.tsx

```typescript
import { Bell, Settings, LogOut } from 'lucide-react';
import { Avatar, AvatarFallback, AvatarImage } from '@/core/components/ui/avatar';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/core/components/ui/dropdown-menu';
import { Button } from '@/core/components/ui/button';
import { useAuth } from '@/core/hooks/useAuth';
import { useNavigate } from 'react-router-dom';

export function Navbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <header className="h-16 border-b bg-white flex items-center justify-between px-6">
      <div className="flex items-center space-x-4">
        <h1 className="text-xl font-semibold">Habilitat</h1>
      </div>

      <div className="flex items-center space-x-4">
        {/* Notifications */}
        <Button variant="ghost" size="icon">
          <Bell className="h-5 w-5" />
        </Button>

        {/* User Menu */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" className="relative h-10 w-10 rounded-full">
              <Avatar>
                <AvatarImage src={user?.avatarUrl} alt={user?.firstName} />
                <AvatarFallback>
                  {user?.firstName?.[0]}
                  {user?.lastName?.[0]}
                </AvatarFallback>
              </Avatar>
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuLabel>
              <div className="flex flex-col space-y-1">
                <p className="text-sm font-medium">{user?.fullName}</p>
                <p className="text-xs text-muted-foreground">{user?.email}</p>
              </div>
            </DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={() => navigate('/profile')}>
              <Settings className="mr-2 h-4 w-4" />
              Perfil
            </DropdownMenuItem>
            <DropdownMenuItem onClick={handleLogout}>
              <LogOut className="mr-2 h-4 w-4" />
              Cerrar sesión
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </header>
  );
}
```

### Sidebar.tsx

```typescript
import { NavLink } from 'react-router-dom';
import { cn } from '@/core/utils/cn';
import {
  Home,
  Users,
  BookOpen,
  FileText,
  BarChart3,
  Settings,
} from 'lucide-react';
import { useAuth } from '@/core/hooks/useAuth';

interface NavItem {
  to: string;
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  adminOnly?: boolean;
}

const navItems: NavItem[] = [
  { to: '/', icon: Home, label: 'Dashboard' },
  { to: '/onboarding', icon: BookOpen, label: 'Onboarding' },
  { to: '/admin/users', icon: Users, label: 'Usuarios', adminOnly: true },
  { to: '/admin/flows', icon: FileText, label: 'Flujos', adminOnly: true },
  { to: '/admin/content', icon: FileText, label: 'Contenido', adminOnly: true },
  { to: '/admin/analytics', icon: BarChart3, label: 'Analytics', adminOnly: true },
  { to: '/admin/settings', icon: Settings, label: 'Configuración', adminOnly: true },
];

export function Sidebar() {
  const { user } = useAuth();
  const isAdmin = user?.role === 'tenant_admin' || user?.role === 'super_admin';

  return (
    <aside className="w-64 bg-white border-r flex flex-col">
      <div className="p-6">
        <img src="/logo.svg" alt="Logo" className="h-8" />
      </div>

      <nav className="flex-1 px-4 space-y-1">
        {navItems.map((item) => {
          // Ocultar items de admin si no es admin
          if (item.adminOnly && !isAdmin) return null;

          return (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                cn(
                  'flex items-center space-x-3 px-3 py-2 rounded-lg transition-colors',
                  isActive
                    ? 'bg-primary text-primary-foreground'
                    : 'text-gray-700 hover:bg-gray-100'
                )
              }
            >
              <item.icon className="h-5 w-5" />
              <span>{item.label}</span>
            </NavLink>
          );
        })}
      </nav>
    </aside>
  );
}
```

## 3. Route Guards (components/guards/)

### ProtectedRoute.tsx

```typescript
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '@/core/hooks/useAuth';
import { LoadingSpinner } from '@/core/components/common/LoadingSpinner';

interface ProtectedRouteProps {
  children: React.ReactNode;
}

export function ProtectedRoute({ children }: ProtectedRouteProps) {
  const { user, isLoading } = useAuth();
  const location = useLocation();

  if (isLoading) {
    return <LoadingSpinner />;
  }

  if (!user) {
    // Redirect a login guardando la ubicación actual
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return <>{children}</>;
}
```

### AdminRoute.tsx

```typescript
import { Navigate } from 'react-router-dom';
import { useAuth } from '@/core/hooks/useAuth';

interface AdminRouteProps {
  children: React.ReactNode;
}

export function AdminRoute({ children }: AdminRouteProps) {
  const { user } = useAuth();

  const isAdmin = user?.role === 'tenant_admin' || user?.role === 'super_admin';

  if (!isAdmin) {
    return <Navigate to="/" replace />;
  }

  return <>{children}</>;
}
```

## 4. Hooks Globales (hooks/)

### useAuth.ts

```typescript
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface User {
  id: number;
  email: string;
  firstName: string;
  lastName: string;
  fullName: string;
  role: string;
  avatarUrl?: string;
  tenantId: number;
}

interface AuthState {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  setAuth: (user: User, token: string) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      token: null,
      isLoading: false,
      setAuth: (user, token) => {
        set({ user, token });
        localStorage.setItem('auth_token', token);
      },
      logout: () => {
        set({ user: null, token: null });
        localStorage.removeItem('auth_token');
        localStorage.removeItem('auth_user');
      },
    }),
    {
      name: 'auth-storage',
    }
  )
);

// Hook conveniente
export function useAuth() {
  return useAuthStore();
}
```

### useTenant.ts

```typescript
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/core/api/client';

interface TenantBranding {
  logo: string | null;
  colors: {
    primary: string;
    secondary: string;
    background: string;
    text: string;
  };
}

interface Tenant {
  id: number;
  name: string;
  subdomain: string;
  branding: TenantBranding;
}

async function fetchTenant(): Promise<Tenant> {
  const { data } = await apiClient.get('/tenants/me');
  return data;
}

export function useTenant() {
  const { data: tenant, isLoading, error } = useQuery({
    queryKey: ['tenant'],
    queryFn: fetchTenant,
    staleTime: 10 * 60 * 1000, // 10 minutos
  });

  return { tenant, isLoading, error };
}
```

### useDebounce.ts

```typescript
import { useEffect, useState } from 'react';

export function useDebounce<T>(value: T, delay: number = 500): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value);

  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => {
      clearTimeout(timer);
    };
  }, [value, delay]);

  return debouncedValue;
}
```

## 5. Theming (theme/)

### theme.ts

```typescript
interface TenantBranding {
  logo: string | null;
  colors: {
    primary: string;
    secondary: string;
    accent?: string;
    background: string;
    text: string;
  };
}

export function applyTenantTheme(branding: TenantBranding) {
  const root = document.documentElement;

  // Convertir hex a RGB para usar con Tailwind opacity
  const hexToRgb = (hex: string): string => {
    const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
    return result
      ? `${parseInt(result[1], 16)} ${parseInt(result[2], 16)} ${parseInt(result[3], 16)}`
      : '0 0 0';
  };

  // Aplicar colores
  root.style.setProperty('--color-primary', hexToRgb(branding.colors.primary));
  root.style.setProperty('--color-secondary', hexToRgb(branding.colors.secondary));

  if (branding.colors.accent) {
    root.style.setProperty('--color-accent', hexToRgb(branding.colors.accent));
  }

  // Favicon
  if (branding.logo) {
    const favicon = document.querySelector("link[rel~='icon']") as HTMLLinkElement;
    if (favicon) {
      favicon.href = branding.logo;
    }
  }
}

export function resetTheme() {
  const root = document.documentElement;
  root.style.removeProperty('--color-primary');
  root.style.removeProperty('--color-secondary');
  root.style.removeProperty('--color-accent');
}
```

## 6. Types Globales (types/)

### api.types.ts

```typescript
export interface ApiResponse<T> {
  data: T;
  success: boolean;
  message?: string;
}

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
}

export interface ApiError {
  success: false;
  error: string;
  detail?: string;
}
```

### auth.types.ts

```typescript
export interface User {
  id: number;
  email: string;
  firstName: string;
  lastName: string;
  fullName: string;
  role: UserRole;
  avatarUrl?: string;
  tenantId: number;
  isEmailVerified: boolean;
}

export type UserRole = 'super_admin' | 'tenant_admin' | 'employee';

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface RegisterData {
  email: string;
  password: string;
  firstName: string;
  lastName: string;
}
```

## 7. Utilidades (utils/)

### format.ts

```typescript
import { format, formatDistanceToNow } from 'date-fns';
import { es } from 'date-fns/locale';

export function formatDate(date: string | Date, formatStr: string = 'dd/MM/yyyy'): string {
  return format(new Date(date), formatStr, { locale: es });
}

export function formatDateTime(date: string | Date): string {
  return format(new Date(date), 'dd/MM/yyyy HH:mm', { locale: es });
}

export function formatRelativeTime(date: string | Date): string {
  return formatDistanceToNow(new Date(date), { addSuffix: true, locale: es });
}

export function formatPercentage(value: number): string {
  return `${Math.round(value)}%`;
}

export function formatNumber(value: number): string {
  return new Intl.NumberFormat('es-ES').format(value);
}
```

### validation.ts

```typescript
export function isValidEmail(email: string): boolean {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
}

export function isStrongPassword(password: string): boolean {
  // Al menos 8 caracteres, 1 mayúscula, 1 minúscula, 1 número
  const passwordRegex = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$/;
  return passwordRegex.test(password);
}

export function truncate(str: string, maxLength: number): string {
  if (str.length <= maxLength) return str;
  return str.slice(0, maxLength) + '...';
}
```

## 8. Componentes Comunes (components/common/)

### LoadingSpinner.tsx

```typescript
import { Loader2 } from 'lucide-react';
import { cn } from '@/core/utils/cn';

interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export function LoadingSpinner({ size = 'md', className }: LoadingSpinnerProps) {
  const sizeClasses = {
    sm: 'h-4 w-4',
    md: 'h-8 w-8',
    lg: 'h-12 w-12',
  };

  return (
    <div className="flex justify-center items-center p-4">
      <Loader2 className={cn('animate-spin text-primary', sizeClasses[size], className)} />
    </div>
  );
}
```

### EmptyState.tsx

```typescript
import { LucideIcon } from 'lucide-react';
import { Button } from '@/core/components/ui/button';

interface EmptyStateProps {
  icon: LucideIcon;
  title: string;
  description: string;
  actionLabel?: string;
  onAction?: () => void;
}

export function EmptyState({
  icon: Icon,
  title,
  description,
  actionLabel,
  onAction,
}: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-12 px-4 text-center">
      <Icon className="h-12 w-12 text-gray-400 mb-4" />
      <h3 className="text-lg font-semibold text-gray-900 mb-2">{title}</h3>
      <p className="text-sm text-gray-600 mb-6 max-w-md">{description}</p>
      {actionLabel && onAction && (
        <Button onClick={onAction}>{actionLabel}</Button>
      )}
    </div>
  );
}
```

## Dependencias

```json
{
  "dependencies": {
    "react": "^18.3.0",
    "react-dom": "^18.3.0",
    "react-router-dom": "^6.20.0",
    "@tanstack/react-query": "^5.15.0",
    "axios": "^1.6.2",
    "zustand": "^4.4.7",
    "date-fns": "^3.0.0",
    "lucide-react": "^0.300.0",
    "@radix-ui/react-avatar": "^1.0.4",
    "@radix-ui/react-dropdown-menu": "^2.0.6",
    "@radix-ui/react-dialog": "^1.0.5",
    "class-variance-authority": "^0.7.0",
    "clsx": "^2.0.0",
    "tailwind-merge": "^2.2.0"
  },
  "devDependencies": {
    "@types/react": "^18.2.45",
    "@types/react-dom": "^18.2.18",
    "@vitejs/plugin-react": "^4.2.1",
    "typescript": "^5.3.3",
    "vite": "^5.0.8",
    "tailwindcss": "^3.4.0",
    "autoprefixer": "^10.4.16",
    "postcss": "^8.4.32"
  }
}
```

## Checklist

- [ ] Setup de Vite + React + TypeScript
- [ ] Configuración de Tailwind CSS
- [ ] Instalación de shadcn/ui
- [ ] Cliente Axios con interceptors
- [ ] Layouts (Root, Auth)
- [ ] Route guards
- [ ] Hooks globales (useAuth, useTenant)
- [ ] Sistema de theming dinámico
- [ ] Componentes UI base (shadcn/ui)
- [ ] Componentes comunes (Loading, Empty, etc.)
- [ ] Types globales
- [ ] Utilidades de formato y validación

## Notas

1. Este módulo debe implementarse **primero**
2. Usar shadcn/ui para componentes base (no reinventar la rueda)
3. El theming dinámico es **crítico** para multitenant
4. Interceptors de Axios manejan auth y tenant automáticamente
5. Tests con Vitest + React Testing Library
