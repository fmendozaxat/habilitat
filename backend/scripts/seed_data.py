#!/usr/bin/env python3
"""
Seed script to populate the database with realistic test data.
Run from backend directory: python scripts/seed_data.py
"""

import sys
import os
from datetime import datetime, timedelta, timezone
from random import choice, randint, uniform

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine
from app.core.security import hash_password

# Import ALL models to ensure relationships are registered
from app.tenants.models import Tenant, TenantBranding
from app.users.models import User, UserInvitation
from app.auth.models import RefreshToken, PasswordResetToken, EmailVerificationToken
from app.onboarding.models import OnboardingFlow, OnboardingModule, OnboardingAssignment, ModuleProgress
from app.content.models import ContentCategory, ContentBlock
from app.notifications.models import EmailLog


def create_tenants(db: Session) -> list[Tenant]:
    """Create sample tenants/organizations."""
    tenants_data = [
        {
            "name": "TechStart Solutions",
            "slug": "techstart",
            "subdomain": "techstart",
            "contact_email": "admin@techstart.com",
            "contact_phone": "+52 55 1234 5678",
            "plan": "business",
            "max_users": 50,
            "max_storage_mb": 5000,
        },
        {
            "name": "Innovación Digital MX",
            "slug": "innovacion-digital",
            "subdomain": "innovacion",
            "contact_email": "contacto@innovaciondigital.mx",
            "contact_phone": "+52 33 9876 5432",
            "plan": "starter",
            "max_users": 25,
            "max_storage_mb": 2500,
        },
        {
            "name": "Grupo Empresarial Norte",
            "slug": "grupo-norte",
            "subdomain": "gruponorte",
            "contact_email": "rh@gruponorte.com",
            "contact_phone": "+52 81 5555 1234",
            "plan": "enterprise",
            "max_users": 200,
            "max_storage_mb": 20000,
        },
    ]

    tenants = []
    for data in tenants_data:
        existing = db.query(Tenant).filter(Tenant.slug == data["slug"]).first()
        if existing:
            tenants.append(existing)
            print(f"  Tenant '{data['name']}' ya existe, omitiendo...")
            continue

        tenant = Tenant(**data)
        db.add(tenant)
        db.flush()
        tenants.append(tenant)
        print(f"  Creado tenant: {data['name']}")

    return tenants


def create_branding(db: Session, tenants: list[Tenant]) -> None:
    """Create branding for tenants."""
    branding_configs = [
        {
            "primary_color": "#3B82F6",
            "secondary_color": "#10B981",
            "accent_color": "#F59E0B",
        },
        {
            "primary_color": "#8B5CF6",
            "secondary_color": "#EC4899",
            "accent_color": "#06B6D4",
        },
        {
            "primary_color": "#EF4444",
            "secondary_color": "#F97316",
            "accent_color": "#22C55E",
        },
    ]

    for i, tenant in enumerate(tenants):
        existing = db.query(TenantBranding).filter(TenantBranding.tenant_id == tenant.id).first()
        if existing:
            print(f"  Branding para '{tenant.name}' ya existe, omitiendo...")
            continue

        branding = TenantBranding(
            tenant_id=tenant.id,
            **branding_configs[i % len(branding_configs)]
        )
        db.add(branding)
        print(f"  Creado branding para: {tenant.name}")


def create_users(db: Session, tenants: list[Tenant]) -> dict[int, list[User]]:
    """Create sample users for each tenant."""
    users_by_tenant = {}

    # Users for first tenant (TechStart)
    techstart_users = [
        {"first_name": "Carlos", "last_name": "Mendoza", "email": "carlos.mendoza@techstart.com", "role": "tenant_admin", "job_title": "Director de RH", "department": "Recursos Humanos"},
        {"first_name": "Ana", "last_name": "García", "email": "ana.garcia@techstart.com", "role": "tenant_admin", "job_title": "Gerente de Onboarding", "department": "Recursos Humanos"},
        {"first_name": "Miguel", "last_name": "López", "email": "miguel.lopez@techstart.com", "role": "employee", "job_title": "Desarrollador Senior", "department": "Tecnología"},
        {"first_name": "Laura", "last_name": "Martínez", "email": "laura.martinez@techstart.com", "role": "employee", "job_title": "Diseñadora UX", "department": "Diseño"},
        {"first_name": "Roberto", "last_name": "Sánchez", "email": "roberto.sanchez@techstart.com", "role": "employee", "job_title": "Analista de Datos", "department": "Tecnología"},
        {"first_name": "María", "last_name": "Hernández", "email": "maria.hernandez@techstart.com", "role": "employee", "job_title": "Product Manager", "department": "Producto"},
        {"first_name": "Jorge", "last_name": "Ramírez", "email": "jorge.ramirez@techstart.com", "role": "employee", "job_title": "DevOps Engineer", "department": "Tecnología"},
        {"first_name": "Patricia", "last_name": "Torres", "email": "patricia.torres@techstart.com", "role": "employee", "job_title": "QA Engineer", "department": "Tecnología"},
        {"first_name": "Fernando", "last_name": "Díaz", "email": "fernando.diaz@techstart.com", "role": "employee", "job_title": "Contador", "department": "Finanzas"},
        {"first_name": "Gabriela", "last_name": "Flores", "email": "gabriela.flores@techstart.com", "role": "employee", "job_title": "Marketing Manager", "department": "Marketing"},
    ]

    # Users for second tenant (Innovación Digital)
    innovacion_users = [
        {"first_name": "Ricardo", "last_name": "Vega", "email": "ricardo.vega@innovacion.mx", "role": "tenant_admin", "job_title": "CEO", "department": "Dirección"},
        {"first_name": "Sofía", "last_name": "Castro", "email": "sofia.castro@innovacion.mx", "role": "tenant_admin", "job_title": "HR Manager", "department": "Recursos Humanos"},
        {"first_name": "Diego", "last_name": "Morales", "email": "diego.morales@innovacion.mx", "role": "employee", "job_title": "Full Stack Developer", "department": "Desarrollo"},
        {"first_name": "Valeria", "last_name": "Ortiz", "email": "valeria.ortiz@innovacion.mx", "role": "employee", "job_title": "Frontend Developer", "department": "Desarrollo"},
        {"first_name": "Andrés", "last_name": "Reyes", "email": "andres.reyes@innovacion.mx", "role": "employee", "job_title": "Backend Developer", "department": "Desarrollo"},
        {"first_name": "Camila", "last_name": "Jiménez", "email": "camila.jimenez@innovacion.mx", "role": "employee", "job_title": "Diseñadora Gráfica", "department": "Diseño"},
    ]

    # Users for third tenant (Grupo Norte)
    grupo_norte_users = [
        {"first_name": "Alejandro", "last_name": "Pérez", "email": "alejandro.perez@gruponorte.com", "role": "tenant_admin", "job_title": "Director General", "department": "Dirección"},
        {"first_name": "Isabel", "last_name": "Ruiz", "email": "isabel.ruiz@gruponorte.com", "role": "tenant_admin", "job_title": "Directora de RH", "department": "Recursos Humanos"},
        {"first_name": "Javier", "last_name": "González", "email": "javier.gonzalez@gruponorte.com", "role": "employee", "job_title": "Gerente de Operaciones", "department": "Operaciones"},
        {"first_name": "Mónica", "last_name": "Silva", "email": "monica.silva@gruponorte.com", "role": "employee", "job_title": "Coordinadora de Capacitación", "department": "Recursos Humanos"},
        {"first_name": "Enrique", "last_name": "Vargas", "email": "enrique.vargas@gruponorte.com", "role": "employee", "job_title": "Gerente de Ventas", "department": "Ventas"},
        {"first_name": "Carmen", "last_name": "Medina", "email": "carmen.medina@gruponorte.com", "role": "employee", "job_title": "Ejecutiva de Cuentas", "department": "Ventas"},
        {"first_name": "Luis", "last_name": "Navarro", "email": "luis.navarro@gruponorte.com", "role": "employee", "job_title": "Analista Financiero", "department": "Finanzas"},
        {"first_name": "Rosa", "last_name": "Guerrero", "email": "rosa.guerrero@gruponorte.com", "role": "employee", "job_title": "Asistente Administrativo", "department": "Administración"},
    ]

    all_users_data = [
        (tenants[0], techstart_users),
        (tenants[1], innovacion_users),
        (tenants[2], grupo_norte_users),
    ]

    password_hash = hash_password("Password123!")

    for tenant, users_data in all_users_data:
        users_by_tenant[tenant.id] = []

        for user_data in users_data:
            existing = db.query(User).filter(User.email == user_data["email"]).first()
            if existing:
                users_by_tenant[tenant.id].append(existing)
                print(f"  Usuario '{user_data['email']}' ya existe, omitiendo...")
                continue

            user = User(
                tenant_id=tenant.id,
                hashed_password=password_hash,
                is_active=True,
                is_email_verified=True,
                **user_data
            )
            db.add(user)
            db.flush()
            users_by_tenant[tenant.id].append(user)
            print(f"  Creado usuario: {user_data['first_name']} {user_data['last_name']}")

    return users_by_tenant


def create_content_categories(db: Session, tenants: list[Tenant]) -> dict[int, list[ContentCategory]]:
    """Create content categories for each tenant."""
    categories_by_tenant = {}

    categories_data = [
        {"name": "Políticas", "slug": "politicas", "description": "Políticas y reglamentos de la empresa", "color": "#3B82F6"},
        {"name": "Cultura", "slug": "cultura", "description": "Valores y cultura organizacional", "color": "#10B981"},
        {"name": "Herramientas", "slug": "herramientas", "description": "Guías de herramientas y software", "color": "#F59E0B"},
        {"name": "Beneficios", "slug": "beneficios", "description": "Información sobre beneficios", "color": "#8B5CF6"},
        {"name": "Procesos", "slug": "procesos", "description": "Procesos y procedimientos", "color": "#EF4444"},
    ]

    for tenant in tenants:
        categories_by_tenant[tenant.id] = []

        for cat_data in categories_data:
            existing = db.query(ContentCategory).filter(
                ContentCategory.tenant_id == tenant.id,
                ContentCategory.slug == cat_data["slug"]
            ).first()

            if existing:
                categories_by_tenant[tenant.id].append(existing)
                continue

            category = ContentCategory(tenant_id=tenant.id, **cat_data)
            db.add(category)
            db.flush()
            categories_by_tenant[tenant.id].append(category)

        print(f"  Creadas {len(categories_data)} categorías para: {tenant.name}")

    return categories_by_tenant


def create_content_blocks(db: Session, tenants: list[Tenant], categories: dict[int, list[ContentCategory]]) -> None:
    """Create content blocks for each tenant."""

    content_templates = [
        {
            "title": "Código de Conducta",
            "description": "Nuestro código de conducta y ética profesional",
            "content_type": "text",
            "content_text": """
# Código de Conducta

## Principios Fundamentales

1. **Integridad**: Actuar con honestidad y transparencia en todas las interacciones.
2. **Respeto**: Tratar a todos los compañeros con dignidad y consideración.
3. **Responsabilidad**: Cumplir con las obligaciones y compromisos adquiridos.
4. **Colaboración**: Trabajar en equipo para alcanzar objetivos comunes.

## Comportamiento Esperado

- Mantener comunicación clara y respetuosa
- Cumplir con los horarios establecidos
- Proteger la información confidencial de la empresa
- Reportar cualquier irregularidad observada

## Consecuencias

El incumplimiento de este código puede resultar en acciones disciplinarias.
            """,
            "category_index": 0,
            "tags": ["conducta", "ética", "valores"],
        },
        {
            "title": "Guía de Slack",
            "description": "Cómo usar Slack para comunicación interna",
            "content_type": "text",
            "content_text": """
# Guía de Slack

## Canales Principales

- **#general**: Anuncios importantes
- **#random**: Conversaciones informales
- **#soporte-ti**: Solicitudes de soporte técnico
- **#rh**: Consultas de Recursos Humanos

## Buenas Prácticas

1. Usa threads para mantener conversaciones organizadas
2. Menciona @channel solo para mensajes urgentes
3. Configura tu estado cuando estés ausente
4. Responde en horario laboral (8am - 6pm)
            """,
            "category_index": 2,
            "tags": ["slack", "comunicación", "herramientas"],
        },
        {
            "title": "Beneficios de Salud",
            "description": "Información sobre seguro médico y beneficios de salud",
            "content_type": "text",
            "content_text": """
# Beneficios de Salud

## Seguro de Gastos Médicos Mayores

- Cobertura nacional e internacional
- Deducible anual: $5,000 MXN
- Coaseguro: 10%
- Suma asegurada: $10,000,000 MXN

## Beneficios Adicionales

- Seguro dental incluido
- Seguro de vida (24 meses de salario)
- Chequeo médico anual
- Programa de bienestar mental

## Cómo Usar tu Seguro

1. Presenta tu credencial en hospitales de la red
2. Para reembolsos, envía facturas a rh@empresa.com
3. Emergencias: Llama a la línea 24/7
            """,
            "category_index": 3,
            "tags": ["salud", "seguro", "beneficios"],
        },
        {
            "title": "Nuestra Historia",
            "description": "Conoce la historia y misión de la empresa",
            "content_type": "text",
            "content_text": """
# Nuestra Historia

## Fundación

Fundada en 2015, nuestra empresa nació con la visión de transformar la manera en que las organizaciones gestionan el talento humano.

## Misión

Empoderar a las empresas con herramientas innovadoras que faciliten el desarrollo y retención del talento.

## Visión

Ser la plataforma líder en gestión de talento en Latinoamérica para 2025.

## Valores

- **Innovación**: Buscamos constantemente mejores soluciones
- **Excelencia**: Nos esforzamos por la calidad en todo lo que hacemos
- **Colaboración**: Creemos en el poder del trabajo en equipo
- **Integridad**: Actuamos con honestidad y transparencia
            """,
            "category_index": 1,
            "tags": ["historia", "misión", "visión", "valores"],
        },
        {
            "title": "Proceso de Vacaciones",
            "description": "Cómo solicitar y gestionar tus vacaciones",
            "content_type": "text",
            "content_text": """
# Proceso de Vacaciones

## Días de Vacaciones

- Primer año: 12 días
- 2-4 años: 14 días
- 5+ años: 16 días
- Prima vacacional: 25%

## Cómo Solicitar

1. Ingresa al sistema de RH
2. Selecciona "Nueva solicitud de vacaciones"
3. Elige las fechas deseadas
4. Espera aprobación de tu manager

## Políticas

- Solicitar con mínimo 2 semanas de anticipación
- Máximo 10 días consecutivos
- No acumulables al siguiente año
            """,
            "category_index": 4,
            "tags": ["vacaciones", "tiempo libre", "procesos"],
        },
    ]

    for tenant in tenants:
        tenant_categories = categories[tenant.id]
        created_count = 0

        for content in content_templates:
            existing = db.query(ContentBlock).filter(
                ContentBlock.tenant_id == tenant.id,
                ContentBlock.title == content["title"]
            ).first()

            if existing:
                continue

            category = tenant_categories[content["category_index"]]

            block = ContentBlock(
                tenant_id=tenant.id,
                title=content["title"],
                description=content["description"],
                content_type=content["content_type"],
                content_text=content["content_text"],
                category_id=category.id,
                tags=content["tags"],
                is_published=True,
            )
            db.add(block)
            created_count += 1

        if created_count > 0:
            print(f"  Creados {created_count} bloques de contenido para: {tenant.name}")


def create_onboarding_flows(db: Session, tenants: list[Tenant]) -> dict[int, list[OnboardingFlow]]:
    """Create onboarding flows for each tenant."""
    flows_by_tenant = {}

    flows_data = [
        {
            "title": "Onboarding General",
            "description": "Proceso de inducción para todos los nuevos empleados",
            "is_active": True,
            "display_order": 1,
        },
        {
            "title": "Onboarding Tecnología",
            "description": "Inducción específica para el equipo de tecnología",
            "is_active": True,
            "display_order": 2,
        },
        {
            "title": "Onboarding Ventas",
            "description": "Capacitación inicial para el equipo comercial",
            "is_active": True,
            "display_order": 3,
        },
    ]

    for tenant in tenants:
        flows_by_tenant[tenant.id] = []

        for flow_data in flows_data:
            existing = db.query(OnboardingFlow).filter(
                OnboardingFlow.tenant_id == tenant.id,
                OnboardingFlow.title == flow_data["title"]
            ).first()

            if existing:
                flows_by_tenant[tenant.id].append(existing)
                continue

            flow = OnboardingFlow(tenant_id=tenant.id, **flow_data)
            db.add(flow)
            db.flush()
            flows_by_tenant[tenant.id].append(flow)

        print(f"  Creados {len(flows_data)} flujos de onboarding para: {tenant.name}")

    return flows_by_tenant


def create_onboarding_modules(db: Session, flows: dict[int, list[OnboardingFlow]]) -> dict[int, list[OnboardingModule]]:
    """Create modules for each onboarding flow."""
    modules_by_flow = {}

    # Modules for General Onboarding
    general_modules = [
        {"title": "Bienvenida", "description": "Video de bienvenida del CEO", "content_type": "video", "content_url": "https://example.com/welcome.mp4", "order": 1, "estimated_minutes": 10},
        {"title": "Nuestra Historia", "description": "Conoce la historia de la empresa", "content_type": "text", "content_text": "Historia y valores de la empresa...", "order": 2, "estimated_minutes": 15},
        {"title": "Políticas y Reglamentos", "description": "Documentos importantes", "content_type": "pdf", "content_url": "https://example.com/policies.pdf", "order": 3, "estimated_minutes": 30},
        {"title": "Beneficios", "description": "Conoce tus beneficios", "content_type": "text", "content_text": "Detalle de beneficios...", "order": 4, "estimated_minutes": 20},
        {"title": "Quiz de Inducción", "description": "Evalúa tu conocimiento", "content_type": "quiz", "quiz_data": {"questions": [{"q": "¿Cuál es nuestra misión?", "options": ["A", "B", "C"], "correct": 0}]}, "order": 5, "estimated_minutes": 15},
    ]

    # Modules for Tech Onboarding
    tech_modules = [
        {"title": "Setup de Ambiente", "description": "Configura tu equipo de desarrollo", "content_type": "text", "content_text": "Guía de setup...", "order": 1, "estimated_minutes": 60},
        {"title": "Git y Control de Versiones", "description": "Nuestro flujo de trabajo con Git", "content_type": "text", "content_text": "Guía de Git...", "order": 2, "estimated_minutes": 30},
        {"title": "Arquitectura del Sistema", "description": "Overview técnico", "content_type": "video", "content_url": "https://example.com/arch.mp4", "order": 3, "estimated_minutes": 45},
        {"title": "Prácticas de Código", "description": "Estándares y convenciones", "content_type": "pdf", "content_url": "https://example.com/coding.pdf", "order": 4, "estimated_minutes": 30},
    ]

    # Modules for Sales Onboarding
    sales_modules = [
        {"title": "Nuestros Productos", "description": "Catálogo de productos y servicios", "content_type": "text", "content_text": "Información de productos...", "order": 1, "estimated_minutes": 45},
        {"title": "Proceso de Ventas", "description": "Pipeline y metodología", "content_type": "video", "content_url": "https://example.com/sales.mp4", "order": 2, "estimated_minutes": 30},
        {"title": "CRM y Herramientas", "description": "Cómo usar el CRM", "content_type": "text", "content_text": "Guía de CRM...", "order": 3, "estimated_minutes": 40},
        {"title": "Técnicas de Negociación", "description": "Tips y estrategias", "content_type": "pdf", "content_url": "https://example.com/negotiation.pdf", "order": 4, "estimated_minutes": 25},
    ]

    all_modules = [general_modules, tech_modules, sales_modules]

    for tenant_id, tenant_flows in flows.items():
        for i, flow in enumerate(tenant_flows):
            modules_by_flow[flow.id] = []
            modules_data = all_modules[i % len(all_modules)]

            for mod_data in modules_data:
                existing = db.query(OnboardingModule).filter(
                    OnboardingModule.flow_id == flow.id,
                    OnboardingModule.title == mod_data["title"]
                ).first()

                if existing:
                    modules_by_flow[flow.id].append(existing)
                    continue

                module = OnboardingModule(flow_id=flow.id, **mod_data)
                db.add(module)
                db.flush()
                modules_by_flow[flow.id].append(module)

    print(f"  Creados módulos para todos los flujos")
    return modules_by_flow


def create_assignments_and_progress(
    db: Session,
    tenants: list[Tenant],
    users_by_tenant: dict[int, list[User]],
    flows_by_tenant: dict[int, list[OnboardingFlow]],
    modules_by_flow: dict[int, list[OnboardingModule]]
) -> None:
    """Create onboarding assignments and progress for employees."""

    statuses = ["not_started", "in_progress", "in_progress", "completed"]

    for tenant in tenants:
        users = users_by_tenant[tenant.id]
        flows = flows_by_tenant[tenant.id]

        # Get admins (assigners)
        admins = [u for u in users if u.role == "tenant_admin"]
        employees = [u for u in users if u.role == "employee"]

        if not admins or not employees or not flows:
            continue

        assignment_count = 0

        for i, employee in enumerate(employees):
            # Assign 1-2 flows to each employee
            num_flows = min(randint(1, 2), len(flows))
            assigned_flows = flows[:num_flows]

            for flow in assigned_flows:
                existing = db.query(OnboardingAssignment).filter(
                    OnboardingAssignment.user_id == employee.id,
                    OnboardingAssignment.flow_id == flow.id
                ).first()

                if existing:
                    continue

                status = statuses[i % len(statuses)]
                assigner = admins[i % len(admins)]

                # Calculate dates
                assigned_at = datetime.now(timezone.utc) - timedelta(days=randint(5, 30))
                started_at = assigned_at + timedelta(days=randint(0, 3)) if status != "not_started" else None
                completed_at = started_at + timedelta(days=randint(3, 10)) if status == "completed" else None
                due_date = assigned_at + timedelta(days=30)

                # Calculate progress
                modules = modules_by_flow.get(flow.id, [])
                if status == "completed":
                    completion_percentage = 100
                elif status == "in_progress":
                    completion_percentage = randint(20, 80)
                else:
                    completion_percentage = 0

                assignment = OnboardingAssignment(
                    tenant_id=tenant.id,
                    flow_id=flow.id,
                    user_id=employee.id,
                    assigned_by=assigner.id,
                    status=status,
                    assigned_at=assigned_at,
                    started_at=started_at,
                    completed_at=completed_at,
                    due_date=due_date,
                    completion_percentage=completion_percentage,
                )
                db.add(assignment)
                db.flush()
                assignment_count += 1

                # Create module progress
                if modules and status != "not_started":
                    num_completed = int(len(modules) * completion_percentage / 100)

                    for j, module in enumerate(modules):
                        is_completed = j < num_completed

                        progress = ModuleProgress(
                            assignment_id=assignment.id,
                            module_id=module.id,
                            is_completed=is_completed,
                            completed_at=started_at + timedelta(days=j) if is_completed else None,
                            time_spent_minutes=randint(10, 60) if is_completed else 0,
                        )
                        db.add(progress)

        print(f"  Creadas {assignment_count} asignaciones para: {tenant.name}")


def main():
    """Main function to run all seed operations."""
    print("\n" + "="*60)
    print("SEED DATA - Habilitat")
    print("="*60 + "\n")

    db = SessionLocal()

    try:
        print("[1/7] Creando tenants...")
        tenants = create_tenants(db)
        db.commit()

        print("\n[2/7] Creando branding...")
        create_branding(db, tenants)
        db.commit()

        print("\n[3/7] Creando usuarios...")
        users_by_tenant = create_users(db, tenants)
        db.commit()

        print("\n[4/7] Creando categorías de contenido...")
        categories = create_content_categories(db, tenants)
        db.commit()

        print("\n[5/7] Creando bloques de contenido...")
        create_content_blocks(db, tenants, categories)
        db.commit()

        print("\n[6/7] Creando flujos de onboarding...")
        flows = create_onboarding_flows(db, tenants)
        db.commit()

        print("\n[7/7] Creando módulos y asignaciones...")
        modules = create_onboarding_modules(db, flows)
        create_assignments_and_progress(db, tenants, users_by_tenant, flows, modules)
        db.commit()

        print("\n" + "="*60)
        print("SEED COMPLETADO EXITOSAMENTE")
        print("="*60)

        print("\n📋 CREDENCIALES DE ACCESO:")
        print("-" * 40)
        print("Password para todos los usuarios: Password123!")
        print("\nUsuarios admin por tenant:")
        for tenant in tenants:
            users = users_by_tenant.get(tenant.id, [])
            admins = [u for u in users if u.role == "tenant_admin"]
            if admins:
                print(f"\n{tenant.name}:")
                for admin in admins:
                    print(f"  - {admin.email}")
        print("-" * 40 + "\n")

    except Exception as e:
        db.rollback()
        print(f"\n❌ Error: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
