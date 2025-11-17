# Habilitat Frontend - Arquitectura Modular

## Descripción General

Frontend de Habilitat construido con React + TypeScript + Vite, organizado en módulos feature-first para máxima escalabilidad y mantenibilidad.

## Stack Tecnológico

- **Framework:** React 18+
- **Language:** TypeScript 5+
- **Build Tool:** Vite 5+
- **Routing:** React Router v6
- **State Management:** Zustand + React Query
- **Styling:** Tailwind CSS 3+
- **UI Components:** shadcn/ui (Radix UI primitives)
- **Forms:** React Hook Form + Zod
- **HTTP Client:** Axios
- **Date/Time:** date-fns
- **Icons:** Lucide React

## Principios de Arquitectura

1. **Feature-First:** Organización por features/módulos (no por tipo de archivo)
2. **Colocación:** Archivos relacionados agrupados juntos
3. **Separación de responsabilidades:** Presentación vs. Lógica vs. Data
4. **Type Safety:** TypeScript en toda la aplicación
5. **Theming Dinámico:** Soporte para branding personalizado por tenant

## Estructura del Proyecto

```
frontend/
├── public/
│   └── assets/
├── src/
│   ├── core/                    # Módulo 1: Core (infraestructura)
│   │   ├── api/                # Cliente HTTP, interceptors
│   │   ├── components/         # Componentes globales (Layout, Navbar, etc.)
│   │   ├── config/             # Configuración global
│   │   ├── contexts/           # React contexts globales
│   │   ├── hooks/              # Hooks globales
│   │   ├── theme/              # Sistema de theming
│   │   ├── types/              # Types globales
│   │   └── utils/              # Utilidades globales
│   │
│   ├── auth/                    # Módulo 2: Autenticación
│   │   ├── components/
│   │   ├── pages/
│   │   ├── api/
│   │   ├── hooks/
│   │   ├── types/
│   │   └── store/
│   │
│   ├── dashboard/               # Módulo 3: Dashboard
│   │   ├── components/
│   │   ├── pages/
│   │   ├── widgets/
│   │   └── hooks/
│   │
│   ├── tenant-settings/         # Módulo 4: Configuración Tenant
│   │   ├── components/
│   │   ├── pages/
│   │   ├── api/
│   │   └── hooks/
│   │
│   ├── users/                   # Módulo 5: Gestión de Usuarios
│   │   ├── components/
│   │   ├── pages/
│   │   ├── api/
│   │   ├── hooks/
│   │   └── types/
│   │
│   ├── onboarding/              # Módulo 6: Onboarding
│   │   ├── employee/           # Vista empleado
│   │   ├── admin/              # Vista admin
│   │   ├── components/
│   │   ├── api/
│   │   ├── hooks/
│   │   └── types/
│   │
│   ├── content/                 # Módulo 7: CMS
│   │   ├── components/
│   │   ├── pages/
│   │   ├── api/
│   │   └── hooks/
│   │
│   ├── analytics/               # Módulo 8: Analytics
│   │   ├── components/
│   │   ├── pages/
│   │   ├── charts/
│   │   ├── api/
│   │   └── hooks/
│   │
│   ├── App.tsx
│   ├── main.tsx
│   └── routes.tsx
│
├── package.json
├── tsconfig.json
├── vite.config.ts
├── tailwind.config.js
└── components.json             # shadcn/ui config
```

## Módulos del Sistema

### 1. Core (Infraestructura)
**Archivo:** `frontend-modulo-1-core.md`
- Cliente HTTP con interceptors
- Layout components (Navbar, Sidebar, Footer)
- Sistema de theming dinámico
- Auth context y guards
- Error boundaries
- Loading states
- Utilidades globales

### 2. Auth (Autenticación)
**Archivo:** `frontend-modulo-2-auth.md`
- Login/Logout
- Registro
- Password reset
- Email verification
- Protected routes
- Auth state management

### 3. Dashboard
**Archivo:** `frontend-modulo-3-dashboard.md`
- Dashboard empleado (mis onboardings)
- Dashboard admin (métricas generales)
- Widgets de progreso
- Notificaciones

### 4. Tenant Settings (Configuración)
**Archivo:** `frontend-modulo-4-tenant-settings.md`
- Configuración general del tenant
- Branding (logo, colores)
- Gestión de subdomain
- Planes y límites

### 5. Users (Gestión de Usuarios)
**Archivo:** `frontend-modulo-5-users.md`
- Listado de usuarios
- Invitar usuarios
- Gestión de roles
- Perfil de usuario

### 6. Onboarding
**Archivo:** `frontend-modulo-6-onboarding.md`
- **Empleado:** Ver y completar onboardings
- **Admin:** Crear y gestionar flujos
- Progreso visual
- Módulos interactivos (quiz, video, etc.)

### 7. Content (CMS)
**Archivo:** `frontend-modulo-7-content.md`
- Crear/editar bloques de contenido
- Upload de archivos
- Categorías y tags
- Búsqueda de contenido

### 8. Analytics (Reportes)
**Archivo:** `frontend-modulo-8-analytics.md`
- Dashboard de métricas
- Gráficos y visualizaciones
- Reportes por flujo/usuario
- Exportación de datos

## Estructura de un Módulo

Cada módulo sigue esta estructura estándar:

```
module-name/
├── components/          # Componentes del módulo
│   ├── ModuleList.tsx
│   ├── ModuleForm.tsx
│   ├── ModuleCard.tsx
│   └── index.ts
├── pages/               # Páginas/rutas del módulo
│   ├── ModuleListPage.tsx
│   ├── ModuleDetailPage.tsx
│   └── index.ts
├── api/                 # API calls específicos
│   ├── module.api.ts
│   └── index.ts
├── hooks/               # Custom hooks del módulo
│   ├── useModule.ts
│   ├── useModuleList.ts
│   └── index.ts
├── types/               # TypeScript types
│   ├── module.types.ts
│   └── index.ts
├── store/               # Estado local (Zustand)
│   └── module.store.ts
├── utils/               # Utilidades del módulo
│   └── module.utils.ts
└── index.ts             # Exports del módulo
```

## Convenciones de Código

### Naming Conventions

- **Componentes:** PascalCase (e.g., `UserList.tsx`)
- **Hooks:** camelCase con prefijo `use` (e.g., `useAuth.ts`)
- **Utilidades:** camelCase (e.g., `formatDate.ts`)
- **Types/Interfaces:** PascalCase (e.g., `User`, `OnboardingFlow`)
- **Constantes:** UPPER_SNAKE_CASE (e.g., `API_BASE_URL`)

### File Organization

```typescript
// ✅ Buena estructura de componente
import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Button } from '@/core/components/ui/button';
import { userApi } from '../api/user.api';
import type { User } from '../types/user.types';

interface UserListProps {
  tenantId: number;
}

export function UserList({ tenantId }: UserListProps) {
  // Hooks
  const { data, isLoading } = useQuery({
    queryKey: ['users', tenantId],
    queryFn: () => userApi.list(tenantId)
  });

  // Early returns
  if (isLoading) return <div>Loading...</div>;

  // Render
  return (
    <div>
      {/* Component JSX */}
    </div>
  );
}
```

### TypeScript Patterns

```typescript
// Types compartidos
export interface User {
  id: number;
  email: string;
  firstName: string;
  lastName: string;
  role: UserRole;
}

export type UserRole = 'super_admin' | 'tenant_admin' | 'employee';

// API Response types
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
```

## Sistema de Theming

### Dynamic Tenant Branding

```typescript
// Aplicar colores del tenant dinámicamente
const applyTenantTheme = (branding: TenantBranding) => {
  document.documentElement.style.setProperty('--color-primary', branding.colors.primary);
  document.documentElement.style.setProperty('--color-secondary', branding.colors.secondary);
  // ...más colores
};
```

### Tailwind + CSS Variables

```css
/* globals.css */
:root {
  --color-primary: 59 130 246; /* RGB */
  --color-secondary: 16 185 129;
}

.btn-primary {
  @apply bg-[rgb(var(--color-primary))];
}
```

## Estado Global vs. Local

### Zustand (Estado Global)

```typescript
// auth/store/auth.store.ts
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface AuthState {
  user: User | null;
  token: string | null;
  setAuth: (user: User, token: string) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      token: null,
      setAuth: (user, token) => set({ user, token }),
      logout: () => set({ user: null, token: null }),
    }),
    { name: 'auth-storage' }
  )
);
```

### React Query (Server State)

```typescript
// users/hooks/useUsers.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { userApi } from '../api/user.api';

export function useUsers(tenantId: number) {
  return useQuery({
    queryKey: ['users', tenantId],
    queryFn: () => userApi.list(tenantId),
  });
}

export function useCreateUser() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: userApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] });
    },
  });
}
```

## Routing

### Protected Routes

```typescript
// routes.tsx
import { createBrowserRouter } from 'react-router-dom';
import { ProtectedRoute } from './core/components/ProtectedRoute';
import { AdminRoute } from './core/components/AdminRoute';

export const router = createBrowserRouter([
  {
    path: '/login',
    element: <LoginPage />,
  },
  {
    path: '/',
    element: <ProtectedRoute><RootLayout /></ProtectedRoute>,
    children: [
      {
        index: true,
        element: <DashboardPage />,
      },
      {
        path: 'onboarding',
        children: [
          { index: true, element: <OnboardingListPage /> },
          { path: ':id', element: <OnboardingDetailPage /> },
        ],
      },
      {
        path: 'admin',
        element: <AdminRoute><AdminLayout /></AdminRoute>,
        children: [
          { path: 'users', element: <UsersPage /> },
          { path: 'flows', element: <FlowsPage /> },
          { path: 'analytics', element: <AnalyticsPage /> },
        ],
      },
    ],
  },
]);
```

## API Client

### Axios Setup con Interceptors

```typescript
// core/api/client.ts
import axios from 'axios';
import { useAuthStore } from '@/auth/store/auth.store';

export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor: Add auth token
apiClient.interceptors.request.use((config) => {
  const token = useAuthStore.getState().token;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor: Handle errors
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      useAuthStore.getState().logout();
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);
```

## Variables de Entorno

```env
# .env.example
VITE_API_URL=http://localhost:8000/api/v1
VITE_APP_NAME=Habilitat
VITE_ENABLE_ANALYTICS=false
```

## Testing

### Testing Stack

- **Unit Tests:** Vitest
- **Component Tests:** React Testing Library
- **E2E Tests:** Playwright

```typescript
// users/components/UserList.test.tsx
import { render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { UserList } from './UserList';

describe('UserList', () => {
  it('renders users', async () => {
    const queryClient = new QueryClient();

    render(
      <QueryClientProvider client={queryClient}>
        <UserList tenantId={1} />
      </QueryClientProvider>
    );

    expect(await screen.findByText('Users')).toBeInTheDocument();
  });
});
```

## Build & Deploy

### Vercel Deployment

```json
// vercel.json
{
  "buildCommand": "npm run build",
  "outputDirectory": "dist",
  "framework": "vite",
  "rewrites": [
    { "source": "/(.*)", "destination": "/index.html" }
  ]
}
```

### Environment por Branch

- **main** → Production (`app.habilitat.com`)
- **staging** → Staging (`staging.habilitat.com`)
- **dev** → Development (`dev.habilitat.com`)

## Guía de Desarrollo

### Setup Inicial

```bash
# Instalar dependencias
npm install

# Configurar .env
cp .env.example .env

# Iniciar dev server
npm run dev
```

### Orden de Desarrollo de Módulos

1. **Core** - Setup base, theming, API client
2. **Auth** - Login y protección de rutas
3. **Dashboard** - Layouts y navegación
4. **Tenant Settings** - Branding dinámico
5. **Users** - Gestión de usuarios
6. **Onboarding** - Feature principal (empleado primero, luego admin)
7. **Content** - CMS
8. **Analytics** - Reportes

### Checklist por Módulo

- [ ] Componentes implementados con TypeScript
- [ ] API calls con React Query
- [ ] Rutas configuradas en router
- [ ] Forms con React Hook Form + Zod
- [ ] Responsive design (mobile-first)
- [ ] Loading y error states
- [ ] Tests unitarios
- [ ] Accesibilidad (a11y)

## Performance

### Code Splitting

```typescript
// Lazy loading de módulos
const OnboardingPage = lazy(() => import('@/onboarding/pages/OnboardingPage'));
const AnalyticsPage = lazy(() => import('@/analytics/pages/AnalyticsPage'));
```

### React Query Cache

```typescript
// Configuración de cache
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutos
      cacheTime: 10 * 60 * 1000, // 10 minutos
    },
  },
});
```

## Accesibilidad

- Usar componentes semánticos de shadcn/ui (basados en Radix)
- Keyboard navigation
- ARIA labels
- Color contrast ratio mínimo 4.5:1

## Estado del Proyecto

- [ ] Módulo 1: Core
- [ ] Módulo 2: Auth
- [ ] Módulo 3: Dashboard
- [ ] Módulo 4: Tenant Settings
- [ ] Módulo 5: Users
- [ ] Módulo 6: Onboarding
- [ ] Módulo 7: Content
- [ ] Módulo 8: Analytics

## Próximos Pasos

1. Leer todos los `frontend-modulo-X-*.md`
2. Setup inicial del proyecto con Vite
3. Implementar módulos en orden sugerido
4. Integrar con backend (API)
5. Testing y deployment

## Recursos

- [React Docs](https://react.dev/)
- [Vite Docs](https://vitejs.dev/)
- [shadcn/ui](https://ui.shadcn.com/)
- [Tailwind CSS](https://tailwindcss.com/)
- [React Query](https://tanstack.com/query/latest)
