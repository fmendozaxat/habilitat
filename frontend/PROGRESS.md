# Progreso del Proyecto Habilitat Frontend

## Fecha: 2024-11-30

## Resumen General

Se migró el frontend de Tailwind CSS a Bootstrap 5 y se corrigieron varios problemas de integración con el backend.

---

## Cambios Realizados

### 1. Migración de Tailwind CSS a Bootstrap 5

- Se removió Tailwind CSS y todas sus dependencias
- Se instaló Bootstrap 5 y React-Bootstrap
- Se actualizaron todos los componentes para usar clases de Bootstrap
- Se creó `src/index.css` con estilos personalizados para Bootstrap

### 2. Correcciones de API Frontend-Backend

#### 2.1 Header X-Tenant-ID
**Archivo:** `src/core/api/client.ts`

Se agregó el header `X-Tenant-ID` en el interceptor de request para soportar multi-tenancy:

```typescript
// Request interceptor - add auth token and tenant ID
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = storage.getAccessToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    // Add tenant ID header for multi-tenant support
    const tenant = storage.getTenant();
    if (tenant?.id) {
      config.headers['X-Tenant-ID'] = tenant.id.toString();
    }
    return config;
  },
  (error) => Promise.reject(error)
);
```

#### 2.2 PaginatedResponse Type
**Archivo:** `src/core/types/index.ts`

Se corrigió la interfaz para coincidir con la respuesta del backend:

```typescript
export interface PaginatedResponse<T> {
  data: T[];      // El backend devuelve 'data', no 'items'
  items?: T[];    // Alias para compatibilidad
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}
```

#### 2.3 UsersPage Fix
**Archivo:** `src/users/pages/UsersPage.tsx`

Se cambió `data?.items` a `data?.data` para coincidir con la respuesta del backend.

#### 2.4 Loading Spinner
**Archivo:** `src/App.tsx`

Se corrigió el spinner de carga que usaba clases de Tailwind:

```typescript
// Antes (Tailwind)
<div className="flex h-screen items-center justify-content-center">
  <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
</div>

// Después (Bootstrap)
<div className="d-flex vh-100 align-items-center justify-content-center">
  <div className="spinner-border text-primary" role="status">
    <span className="visually-hidden">Cargando...</span>
  </div>
</div>
```

---

## Cambios en el Backend

### 1. LoginResponse con Tenant
**Archivo:** `backend/app/auth/schemas.py`

Se agregó `TenantAuthResponse` y se incluyó en `LoginResponse`:

```python
class TenantAuthResponse(BaseSchema):
    id: int
    name: str
    slug: str
    plan: str

class LoginResponse(BaseSchema):
    access_token: str
    refresh_token: str
    expires_in: int
    token_type: str = "Bearer"
    user: UserAuthResponse
    tenant: TenantAuthResponse  # Agregado
```

### 2. Router de Auth
**Archivo:** `backend/app/auth/router.py`

Se modificó el endpoint de login para devolver el tenant:

```python
from app.tenants.service import TenantService

# En login endpoint:
tenant = TenantService.get_tenant_by_id(db, user.tenant_id)

return LoginResponse(
    # ... otros campos ...
    tenant=TenantAuthResponse(
        id=tenant.id,
        name=tenant.name,
        slug=tenant.slug,
        plan=tenant.plan
    )
)
```

### 3. UserListResponse
**Archivo:** `backend/app/users/schemas.py`

Se agregó `created_at` al schema de lista de usuarios:

```python
class UserListResponse(BaseSchema):
    id: int
    email: str
    first_name: str
    last_name: str
    full_name: str
    avatar_url: str | None
    job_title: str | None
    department: str | None
    role: str
    is_active: bool
    created_at: datetime  # Agregado para evitar error en formatDate
```

### 4. Script de Seed Data
**Archivo:** `backend/scripts/seed_data.py`

Se creó un script para poblar la base de datos con datos de prueba:
- 3 tenants con branding
- Múltiples usuarios por tenant (admin, empleados)
- Categorías de contenido y bloques
- Flujos de onboarding con módulos
- Asignaciones de onboarding

---

## Usuarios de Prueba

### Tenant 1: "Mi Empresa" (slug: mi-empresa)
| Email | Password | Rol |
|-------|----------|-----|
| admin@test.com | Admin123! | tenant_admin |
| carlos.rodriguez@miempresa.com | Test1234! | employee |
| maria.gonzalez@miempresa.com | Test1234! | employee |
| ana.martinez@miempresa.com | Test1234! | employee |
| pedro.sanchez@miempresa.com | Test1234! | employee |
| laura.fernandez@miempresa.com | Test1234! | employee |
| diego.lopez@miempresa.com | Test1234! | employee |
| sofia.ramirez@miempresa.com | Test1234! | employee |
| miguel.torres@miempresa.com | Test1234! | employee |
| valentina.diaz@miempresa.com | Test1234! | employee |
| andres.moreno@miempresa.com | Test1234! | employee |
| camila.ruiz@miempresa.com | Test1234! | employee |
| jorge.herrera@miempresa.com | Test1234! | employee |
| daniela.castro@miempresa.com | Test1234! | employee |
| ricardo.vargas@miempresa.com | Test1234! | employee |
| monica.silva@miempresa.com | Test1234! | employee |

---

## Estado Actual

### Funcionalidades Verificadas
- [x] Login funciona correctamente
- [x] Se devuelve tenant en respuesta de login
- [x] Header X-Tenant-ID se envía en todas las peticiones
- [x] Lista de usuarios se muestra correctamente
- [x] Paginación funciona
- [x] Filtros de usuarios funcionan
- [x] Spinner de carga visible

### Pendientes / Issues Conocidos
- [ ] El backend puede colgarse después de mucho tiempo (requiere reinicio)
- [ ] Verificar otros módulos (Onboarding, Content, Analytics)

---

## Cómo Correr el Proyecto

### Backend
```bash
cd /home/fercho/projects-cw/habilitat/backend
source venv/bin/activate
uvicorn main:app --reload --port 8000
```

### Frontend
```bash
cd /home/fercho/projects-cw/habilitat/frontend
npm run dev
```

### Poblar Base de Datos (si es necesario)
```bash
cd /home/fercho/projects-cw/habilitat/backend
source venv/bin/activate
python scripts/seed_data.py
```

---

## Estructura del Frontend

```
frontend/
├── src/
│   ├── analytics/       # Módulo de analytics
│   ├── assets/          # Recursos estáticos
│   ├── auth/            # Autenticación
│   │   ├── api/         # API calls
│   │   ├── hooks/       # useAuthStore
│   │   └── pages/       # Login, Register, etc.
│   ├── content/         # Gestión de contenido
│   ├── core/            # Componentes y utilidades compartidas
│   │   ├── api/         # Cliente axios
│   │   ├── components/  # Componentes UI reutilizables
│   │   ├── config/      # Constantes y configuración
│   │   ├── types/       # TypeScript types
│   │   └── utils/       # Utilidades (storage, formatters)
│   ├── dashboard/       # Dashboard principal
│   ├── onboarding/      # Flujos de onboarding
│   ├── users/           # Gestión de usuarios
│   ├── App.tsx          # Router principal
│   ├── main.tsx         # Entry point
│   └── index.css        # Estilos globales Bootstrap
├── .env                 # Variables de entorno
├── package.json
└── vite.config.ts
```

---

## Notas Importantes

1. **Multi-tenancy**: El sistema es multi-tenant. Cada petición debe incluir el header `X-Tenant-ID`.

2. **Autenticación**: JWT con access_token (30 min) y refresh_token (7 días).

3. **Bootstrap 5**: Se usa Bootstrap 5 con React-Bootstrap para los componentes UI.

4. **React Query**: Se usa TanStack Query para el manejo de estado del servidor.

5. **Zustand**: Se usa para el estado global de autenticación.
