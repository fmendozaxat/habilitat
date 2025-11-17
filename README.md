# Habilitat - Plataforma de Onboarding Multitenant

## Descripción General

Habilitat es una plataforma profesional de onboarding multitenant que permite a las empresas personalizar completamente la experiencia de incorporación de nuevos empleados con colores, imágenes y contenido propios.

## Arquitectura del Backend

### Stack Tecnológico

- **Framework:** FastAPI 0.104+
- **ORM:** SQLAlchemy 2.0+
- **Base de datos:** PostgreSQL 15+
- **Migraciones:** Alembic
- **Autenticación:** JWT (python-jose)
- **Storage:** AWS S3 / Cloudinary
- **Email:** SendGrid / Resend
- **Testing:** Pytest
- **Validación:** Pydantic v2

### Principios de Arquitectura

1. **Modularidad:** Cada módulo es independiente y cohesivo (máx 5000 líneas)
2. **Separación de responsabilidades:** Cada módulo tiene un propósito claro
3. **Dependency Injection:** Uso de FastAPI's Depends
4. **Clean Architecture:** Separación de capas (API, Business Logic, Data)
5. **Multitenant:** Aislamiento de datos por tenant en toda la aplicación

## Estructura de Módulos

```
backend/
├── app/
│   ├── core/                 # Módulo 1: Infraestructura base
│   ├── auth/                 # Módulo 2: Autenticación y autorización
│   ├── tenants/              # Módulo 3: Gestión de tenants
│   ├── users/                # Módulo 4: Gestión de usuarios
│   ├── onboarding/           # Módulo 5: Flujos de onboarding
│   ├── content/              # Módulo 6: CMS y gestión de contenido
│   ├── analytics/            # Módulo 7: Reportes y métricas
│   └── notifications/        # Módulo 8: Sistema de notificaciones
├── tests/
├── alembic/
├── requirements.txt
└── main.py
```

## Módulos del Sistema

### 1. Core (Infraestructura)
**Archivo:** `modulo-1-core.md`
- Configuración global
- Base de datos y sesiones
- Middlewares
- Utils y helpers comunes
- Excepciones personalizadas
- Storage (S3/Cloudinary)

### 2. Auth (Autenticación)
**Archivo:** `modulo-2-auth.md`
- Login/Logout
- JWT tokens (access + refresh)
- Password reset
- Verificación de email
- Permisos y roles

### 3. Tenants (Multitenant)
**Archivo:** `modulo-3-tenants.md`
- CRUD de organizaciones/empresas
- Configuración de tenant (subdominio, branding)
- Middleware de resolución de tenant
- Personalización (colores, logos, imágenes)

### 4. Users (Usuarios)
**Archivo:** `modulo-4-users.md`
- CRUD de usuarios
- Perfil de usuario
- Roles dentro del tenant (admin, empleado)
- Invitaciones de usuarios

### 5. Onboarding (Flujos)
**Archivo:** `modulo-5-onboarding.md`
- Gestión de flujos de onboarding
- Módulos/pasos del onboarding
- Asignación de onboarding a empleados
- Tracking de progreso
- Completación de tareas

### 6. Content (CMS)
**Archivo:** `modulo-6-content.md`
- Gestión de contenido (texto, imágenes, videos, PDFs)
- Templates de contenido
- Bloques de contenido reutilizables
- Versionado de contenido

### 7. Analytics (Reportes)
**Archivo:** `modulo-7-analytics.md`
- Dashboard de métricas
- Reportes de progreso por empleado
- Reportes de completación por módulo
- Analytics de uso de la plataforma

### 8. Notifications (Notificaciones)
**Archivo:** `modulo-8-notifications.md`
- Envío de emails
- Templates de emails
- Cola de notificaciones
- Notificaciones de eventos (bienvenida, recordatorios, etc.)

## Dependencias entre Módulos

```
Core (base para todos)
  ↓
Auth ← Tenants
  ↓       ↓
Users ← ← ←
  ↓
Onboarding → Content
  ↓            ↓
Analytics  Notifications
```

## Estrategia Multitenant

**Enfoque:** Discriminador a nivel de base de datos (tenant_id en todas las tablas)

**Ventajas:**
- Más simple para MVP
- Una sola base de datos
- Fácil de escalar horizontalmente después

**Implementación:**
- Middleware que resuelve el tenant desde subdomain/header
- Filtros automáticos en queries (tenant_id)
- Foreign keys respetan el tenant_id

## Variables de Entorno

```env
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/habilitat

# JWT
JWT_SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# Storage
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_BUCKET_NAME=
AWS_REGION=

# Email
SENDGRID_API_KEY=
FROM_EMAIL=noreply@habilitat.com

# App
APP_ENV=development
API_PREFIX=/api/v1
CORS_ORIGINS=http://localhost:3000
```

## Estándares de Código

### Estructura de un Módulo

```
module_name/
├── __init__.py
├── models.py          # SQLAlchemy models
├── schemas.py         # Pydantic schemas (request/response)
├── service.py         # Business logic
├── router.py          # FastAPI routes/endpoints
├── dependencies.py    # FastAPI dependencies
├── exceptions.py      # Custom exceptions
└── utils.py           # Module-specific utilities
```

### Convenciones de Naming

- **Modelos:** PascalCase (e.g., `TenantConfig`)
- **Schemas:** PascalCase + sufijo (e.g., `TenantCreate`, `TenantResponse`)
- **Funciones:** snake_case (e.g., `get_tenant_by_id`)
- **Rutas:** kebab-case (e.g., `/api/v1/tenants/config`)
- **Variables:** snake_case (e.g., `current_user`)

### Estructura de Endpoint

```python
@router.get("/{id}", response_model=schemas.EntityResponse)
async def get_entity(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant: Tenant = Depends(get_current_tenant)
):
    """
    Retrieve entity by ID.

    - Requires authentication
    - Scoped to current tenant
    """
    entity = service.get_entity(db, id, tenant.id)
    if not entity:
        raise EntityNotFoundException()
    return entity
```

## Testing

- Cada módulo debe tener su carpeta de tests
- Coverage mínimo: 80%
- Tests de integración para endpoints críticos
- Fixtures para datos de prueba

## Guía de Desarrollo

### 1. Setup Inicial

```bash
# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Instalar dependencias
pip install -r requirements.txt

# Configurar .env
cp .env.example .env

# Crear base de datos
alembic upgrade head

# Correr servidor
uvicorn main:app --reload
```

### 2. Orden de Desarrollo de Módulos

1. **Core** - Base para todo
2. **Tenants** - Infraestructura multitenant
3. **Auth** - Autenticación
4. **Users** - Gestión de usuarios
5. **Content** - CMS
6. **Onboarding** - Flujos principales
7. **Notifications** - Sistema de notificaciones
8. **Analytics** - Reportes

### 3. Checklist por Módulo

- [ ] Modelos definidos con relaciones correctas
- [ ] Schemas de request/response validados
- [ ] Service layer con business logic
- [ ] Endpoints CRUD implementados
- [ ] Middleware de tenant aplicado donde corresponda
- [ ] Tests unitarios y de integración
- [ ] Documentación de API (docstrings)
- [ ] Migraciones de Alembic creadas

## Documentación de API

Una vez corriendo, la documentación interactiva está disponible en:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

## Estado del Proyecto

- [ ] Módulo 1: Core
- [ ] Módulo 2: Auth
- [ ] Módulo 3: Tenants
- [ ] Módulo 4: Users
- [ ] Módulo 5: Onboarding
- [ ] Módulo 6: Content
- [ ] Módulo 7: Analytics
- [ ] Módulo 8: Notifications

## Próximos Pasos

1. Leer todos los `modulo-X-*.md` para entender requerimientos
2. Implementar módulos en el orden sugerido
3. Hacer pull request por módulo completado
4. Revisión y ajuste de requerimientos después de MVP funcional

## Contacto y Soporte

Para dudas sobre la arquitectura o requerimientos específicos, consultar los archivos individuales de cada módulo.
