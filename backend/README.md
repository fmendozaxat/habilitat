# Habilitat Backend

Backend API para la plataforma de onboarding multitenant Habilitat, construido con FastAPI, SQLAlchemy, y PostgreSQL.

## Stack Tecnológico

- **Framework:** FastAPI 0.104+
- **ORM:** SQLAlchemy 2.0+
- **Base de datos:** PostgreSQL 15+
- **Migraciones:** Alembic
- **Autenticación:** JWT (python-jose)
- **Storage:** AWS S3 / Cloudinary
- **Email:** SendGrid
- **Testing:** Pytest

## Estructura del Proyecto

```
backend/
├── app/
│   ├── core/              # Módulo core (infraestructura base)
│   │   ├── config.py      # Configuración y settings
│   │   ├── database.py    # SQLAlchemy setup
│   │   ├── models.py      # Base models y mixins
│   │   ├── schemas.py     # Schemas base de Pydantic
│   │   ├── exceptions.py  # Excepciones personalizadas
│   │   ├── security.py    # Password hashing y JWT
│   │   ├── storage.py     # Servicio de storage (S3/Cloudinary)
│   │   ├── middleware.py  # Middlewares customizados
│   │   ├── utils.py       # Utilidades comunes
│   │   ├── enums.py       # Enums globales
│   │   └── constants.py   # Constantes globales
│   ├── auth/              # TODO: Módulo de autenticación
│   ├── tenants/           # TODO: Módulo de tenants
│   ├── users/             # TODO: Módulo de usuarios
│   └── ...                # Otros módulos
├── tests/
│   ├── core/
│   │   ├── test_security.py
│   │   └── test_utils.py
│   └── test_main.py
├── alembic/               # Migraciones de base de datos
│   ├── versions/
│   └── env.py
├── main.py               # Punto de entrada de la aplicación
├── requirements.txt      # Dependencias de Python
├── .env.example         # Ejemplo de variables de entorno
└── alembic.ini          # Configuración de Alembic
```

## Instalación y Configuración

### Prerequisitos

- Python 3.11+
- PostgreSQL 15+
- pip o poetry

### 1. Clonar el Repositorio

```bash
git clone <repository-url>
cd habilitat/backend
```

### 2. Crear Entorno Virtual

```bash
# Crear entorno virtual
python -m venv venv

# Activar entorno virtual
# En Linux/Mac:
source venv/bin/activate

# En Windows:
venv\Scripts\activate
```

### 3. Instalar Dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar Variables de Entorno

```bash
# Copiar archivo de ejemplo
cp .env.example .env

# Editar .env con tus valores
nano .env  # o usar tu editor preferido
```

Variables críticas a configurar:

```env
# Base de datos
DATABASE_URL=postgresql://user:password@localhost:5432/habilitat

# JWT
JWT_SECRET_KEY=tu-clave-secreta-super-segura

# CORS
CORS_ORIGINS=["http://localhost:3000"]
```

### 5. Crear Base de Datos

```bash
# Crear base de datos PostgreSQL
createdb habilitat

# O usando psql:
psql -U postgres
CREATE DATABASE habilitat;
\q
```

### 6. Ejecutar Migraciones

```bash
# Inicializar Alembic (solo primera vez)
alembic upgrade head
```

## Ejecución

### Modo Desarrollo

```bash
# Opción 1: Con uvicorn directamente
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Opción 2: Ejecutar main.py
python main.py
```

La aplicación estará disponible en:
- API: http://localhost:8000
- Documentación Swagger: http://localhost:8000/api/v1/docs
- Documentación ReDoc: http://localhost:8000/api/v1/redoc

### Modo Producción

```bash
# Instalar servidor ASGI de producción
pip install gunicorn

# Ejecutar con Gunicorn
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

## Testing

### Ejecutar Tests

```bash
# Ejecutar todos los tests
pytest

# Ejecutar con coverage
pytest --cov=app --cov-report=html

# Ejecutar tests de un módulo específico
pytest tests/core/test_security.py

# Ejecutar con verbose
pytest -v
```

### Coverage Report

Después de ejecutar con coverage, abre `htmlcov/index.html` en tu navegador para ver el reporte detallado.

## Migraciones de Base de Datos

### Crear Nueva Migración

```bash
# Crear migración automática (detecta cambios en modelos)
alembic revision --autogenerate -m "Descripción del cambio"

# Crear migración manual
alembic revision -m "Descripción del cambio"
```

### Aplicar Migraciones

```bash
# Aplicar todas las migraciones pendientes
alembic upgrade head

# Aplicar una migración específica
alembic upgrade <revision_id>

# Revertir última migración
alembic downgrade -1

# Revertir todas las migraciones
alembic downgrade base
```

### Ver Historial de Migraciones

```bash
# Ver historial
alembic history

# Ver estado actual
alembic current
```

## Desarrollo

### Agregar Nuevo Módulo

1. Crear estructura de directorios:

```bash
mkdir -p app/nuevo_modulo
touch app/nuevo_modulo/__init__.py
touch app/nuevo_modulo/models.py
touch app/nuevo_modulo/schemas.py
touch app/nuevo_modulo/service.py
touch app/nuevo_modulo/router.py
```

2. Implementar modelos en `models.py`
3. Definir schemas en `schemas.py`
4. Implementar lógica de negocio en `service.py`
5. Crear endpoints en `router.py`
6. Registrar router en `main.py`

### Estándares de Código

- **Nombres de modelos:** PascalCase (e.g., `TenantConfig`)
- **Nombres de funciones:** snake_case (e.g., `get_user_by_id`)
- **Nombres de rutas:** kebab-case (e.g., `/api/v1/users/profile`)
- **Docstrings:** Usar formato Google o NumPy

### Formateo y Linting

```bash
# Formatear código con Black
black app/ tests/

# Linting con Flake8
flake8 app/ tests/

# Type checking con MyPy
mypy app/
```

## Características Implementadas

### Módulo Core ✅

- ✅ Configuración con Pydantic Settings
- ✅ SQLAlchemy setup y gestión de sesiones
- ✅ Base models con mixins (Timestamp, Tenant, SoftDelete)
- ✅ Schemas base para paginación y respuestas
- ✅ Excepciones personalizadas
- ✅ Middleware de tenant resolution
- ✅ Middleware de logging y seguridad
- ✅ Security utils (password hashing, JWT)
- ✅ Storage service (S3/Cloudinary)
- ✅ Utilidades comunes
- ✅ Enums y constantes globales
- ✅ Tests con >80% coverage

### Módulo Auth ✅

- ✅ Login/Logout con JWT
- ✅ Access y Refresh tokens
- ✅ Password reset flow
- ✅ Email verification tokens
- ✅ Role-based dependencies

### Módulo Tenants ✅

- ✅ CRUD de organizaciones
- ✅ Gestión de branding
- ✅ Middleware de resolución de tenant
- ✅ Límites de usuarios y storage

### Módulo Users ✅

- ✅ CRUD de usuarios
- ✅ Perfil de usuario (avatar, phone, job_title, department)
- ✅ Cambio de contraseña
- ✅ Sistema de invitaciones
- ✅ Upload de avatar
- ✅ Filtros y búsqueda
- ✅ Validación de límites de tenant

### Próximos Módulos

- ⏳ Módulo Onboarding (Flujos de onboarding)
- ⏳ Módulo Content (CMS)
- ⏳ Módulo Analytics (Reportes)
- ⏳ Módulo Notifications (Sistema de notificaciones)

## API Endpoints

### Actuales

- `GET /` - Root endpoint (health check)
- `GET /health` - Health check detallado
- `GET /api/v1/` - API root

### Por Implementar

Ver documentación en `/api/v1/docs` una vez que los módulos estén implementados.

## Troubleshooting

### Error de Conexión a Base de Datos

```bash
# Verificar que PostgreSQL esté corriendo
sudo service postgresql status

# Verificar conexión
psql -U postgres -d habilitat
```

### Error de Migraciones

```bash
# Limpiar y recrear base de datos
dropdb habilitat
createdb habilitat
alembic upgrade head
```

### Tests Fallan

```bash
# Limpiar caché de pytest
pytest --cache-clear

# Reinstalar dependencias
pip install -r requirements.txt --force-reinstall
```

## Contribuir

1. Crear rama feature: `git checkout -b feature/nueva-funcionalidad`
2. Hacer cambios y commit: `git commit -m "Agregar nueva funcionalidad"`
3. Ejecutar tests: `pytest`
4. Push: `git push origin feature/nueva-funcionalidad`
5. Crear Pull Request

## Licencia

[Especificar licencia]

## Contacto

[Información de contacto del equipo]
