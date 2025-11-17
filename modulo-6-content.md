# Módulo 6: Content (CMS y Gestión de Contenido)

## Descripción

El módulo Content proporciona un CMS simple para que los tenants creen y gestionen contenido reutilizable: texto, imágenes, videos, PDFs. Este contenido puede ser referenciado desde los módulos de onboarding.

**Límite de líneas:** ~2500-3500 líneas

## Responsabilidades

1. CRUD de bloques de contenido (ContentBlock)
2. Upload de archivos (imágenes, PDFs, videos)
3. Gestión de templates de contenido
4. Categorización de contenido
5. Búsqueda y filtrado de contenido
6. Versionado básico de contenido (opcional para MVP)

## Estructura de Archivos

```
app/content/
├── __init__.py
├── models.py              # ContentBlock, ContentCategory
├── schemas.py             # Request/Response schemas
├── service.py             # Lógica de negocio
├── router.py              # Endpoints
├── exceptions.py          # Excepciones
└── utils.py               # Utilidades (procesamiento de archivos)
```

## 1. Modelos (models.py)

### ContentCategory Model

```python
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.core.models import BaseModel, TimestampMixin, TenantMixin

class ContentCategory(BaseModel, TimestampMixin, TenantMixin):
    """
    Categorías para organizar contenido
    """
    __tablename__ = "content_categories"

    name = Column(String(100), nullable=False)
    slug = Column(String(100), nullable=False, index=True)
    description = Column(String(500), nullable=True)

    # Color para UI (hex)
    color = Column(String(7), default="#6B7280", nullable=False)

    # Relationships
    content_blocks = relationship("ContentBlock", back_populates="category")

    def __repr__(self):
        return f"<ContentCategory {self.name}>"
```

### ContentBlock Model

```python
from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, JSON
from app.core.enums import ContentType

class ContentBlock(BaseModel, TimestampMixin, TenantMixin, SoftDeleteMixin):
    """
    Bloque de contenido reutilizable
    """
    __tablename__ = "content_blocks"

    # Basic info
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)

    # Content type
    content_type = Column(String(50), nullable=False)  # text, image, video, pdf, link, embed

    # Content data
    content_text = Column(Text, nullable=True)  # Para type=text
    content_url = Column(String(500), nullable=True)  # Para archivos, videos, links
    content_metadata = Column(JSON, nullable=True)
    """
    Metadata según tipo:
    - image: {width, height, size_bytes, alt_text}
    - video: {duration_seconds, thumbnail_url, provider}
    - pdf: {page_count, size_bytes}
    - embed: {provider, embed_code}
    """

    # Organization
    category_id = Column(Integer, ForeignKey("content_categories.id", ondelete="SET NULL"), nullable=True)

    # Tags para búsqueda
    tags = Column(JSON, default=[], nullable=False)  # ["bienvenida", "cultura", "beneficios"]

    # Status
    is_published = Column(Boolean, default=True, nullable=False)

    # Relationships
    category = relationship("ContentCategory", back_populates="content_blocks")
    onboarding_modules = relationship("OnboardingModule", back_populates="content", foreign_keys="OnboardingModule.content_id")

    def __repr__(self):
        return f"<ContentBlock {self.title} ({self.content_type})>"
```

## 2. Schemas (schemas.py)

### Request Schemas

```python
from pydantic import BaseModel, Field, HttpUrl
from app.core.schemas import BaseSchema, PaginationParams

# Category
class ContentCategoryCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    slug: str | None = None  # Auto-generado
    description: str | None = Field(None, max_length=500)
    color: str = Field("#6B7280", regex=r'^#[0-9A-Fa-f]{6}$')

class ContentCategoryUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=100)
    description: str | None = None
    color: str | None = Field(None, regex=r'^#[0-9A-Fa-f]{6}$')

# ContentBlock
class ContentBlockCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str | None = None
    content_type: str = Field(..., regex=r'^(text|image|video|pdf|link|embed)$')
    content_text: str | None = None
    content_url: str | None = None
    content_metadata: dict | None = None
    category_id: int | None = None
    tags: list[str] = []
    is_published: bool = True

class ContentBlockUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = None
    content_text: str | None = None
    content_url: str | None = None
    content_metadata: dict | None = None
    category_id: int | None = None
    tags: list[str] | None = None
    is_published: bool | None = None

# Filters
class ContentFilterParams(PaginationParams):
    search: str | None = None
    content_type: str | None = None
    category_id: int | None = None
    tags: list[str] | None = None
    is_published: bool | None = None
```

### Response Schemas

```python
from datetime import datetime

class ContentCategoryResponse(BaseSchema):
    id: int
    name: str
    slug: str
    description: str | None
    color: str
    created_at: datetime

class ContentBlockResponse(BaseSchema):
    id: int
    tenant_id: int
    title: str
    description: str | None
    content_type: str
    content_text: str | None
    content_url: str | None
    content_metadata: dict | None
    category_id: int | None
    category: ContentCategoryResponse | None
    tags: list[str]
    is_published: bool
    created_at: datetime
    updated_at: datetime

class ContentBlockListResponse(BaseSchema):
    """Respuesta simplificada para listados"""
    id: int
    title: str
    content_type: str
    category_id: int | None
    category_name: str | None
    tags: list[str]
    is_published: bool
    created_at: datetime

class FileUploadResponse(BaseSchema):
    url: str
    content_type: str
    size_bytes: int
    metadata: dict
```

## 3. Service (service.py)

### ContentService Class

```python
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from app.core.exceptions import NotFoundException, AlreadyExistsException
from app.content.models import ContentBlock, ContentCategory
from app.content import schemas
from app.core.utils import slugify
from datetime import datetime

class ContentService:
    """Servicio de gestión de contenido"""

    # Categories

    @staticmethod
    def create_category(db: Session, tenant_id: int, data: schemas.ContentCategoryCreate) -> ContentCategory:
        """Crear categoría"""
        # Auto-generar slug si no se proporciona
        slug = data.slug or slugify(data.name)

        # Validar slug único para el tenant
        existing = db.query(ContentCategory).filter(
            ContentCategory.tenant_id == tenant_id,
            ContentCategory.slug == slug
        ).first()

        if existing:
            raise AlreadyExistsException(f"Categoría con slug '{slug}'")

        category = ContentCategory(
            **data.model_dump(exclude={'slug'}),
            slug=slug,
            tenant_id=tenant_id
        )

        db.add(category)
        db.commit()
        db.refresh(category)

        return category

    @staticmethod
    def get_category(db: Session, category_id: int, tenant_id: int) -> ContentCategory:
        """Obtener categoría por ID"""
        category = db.query(ContentCategory).filter(
            ContentCategory.id == category_id,
            ContentCategory.tenant_id == tenant_id
        ).first()

        if not category:
            raise NotFoundException("Categoría")

        return category

    @staticmethod
    def list_categories(db: Session, tenant_id: int) -> list[ContentCategory]:
        """Listar categorías del tenant"""
        return db.query(ContentCategory).filter(
            ContentCategory.tenant_id == tenant_id
        ).order_by(ContentCategory.name).all()

    @staticmethod
    def update_category(
        db: Session,
        category_id: int,
        tenant_id: int,
        data: schemas.ContentCategoryUpdate
    ) -> ContentCategory:
        """Actualizar categoría"""
        category = ContentService.get_category(db, category_id, tenant_id)

        update_data = data.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(category, field, value)

        db.commit()
        db.refresh(category)

        return category

    @staticmethod
    def delete_category(db: Session, category_id: int, tenant_id: int) -> bool:
        """Eliminar categoría (si no tiene contenido asociado)"""
        category = ContentService.get_category(db, category_id, tenant_id)

        if category.content_blocks:
            raise ValidationException("No se puede eliminar una categoría con contenido asociado")

        db.delete(category)
        db.commit()

        return True

    # Content Blocks

    @staticmethod
    def create_content_block(
        db: Session,
        tenant_id: int,
        data: schemas.ContentBlockCreate
    ) -> ContentBlock:
        """Crear bloque de contenido"""
        block = ContentBlock(
            **data.model_dump(),
            tenant_id=tenant_id
        )

        db.add(block)
        db.commit()
        db.refresh(block)

        return block

    @staticmethod
    def get_content_block(db: Session, block_id: int, tenant_id: int) -> ContentBlock:
        """Obtener bloque por ID"""
        block = db.query(ContentBlock).filter(
            ContentBlock.id == block_id,
            ContentBlock.tenant_id == tenant_id
        ).first()

        if not block:
            raise NotFoundException("Bloque de contenido")

        return block

    @staticmethod
    def list_content_blocks(
        db: Session,
        tenant_id: int,
        filters: schemas.ContentFilterParams
    ) -> tuple[list[ContentBlock], int]:
        """
        Listar bloques con filtros y paginación

        Returns:
            (blocks, total_count)
        """
        query = db.query(ContentBlock).filter(ContentBlock.tenant_id == tenant_id)

        # Filtros
        if filters.search:
            search_term = f"%{filters.search}%"
            query = query.filter(
                or_(
                    ContentBlock.title.ilike(search_term),
                    ContentBlock.description.ilike(search_term),
                    ContentBlock.content_text.ilike(search_term)
                )
            )

        if filters.content_type:
            query = query.filter(ContentBlock.content_type == filters.content_type)

        if filters.category_id:
            query = query.filter(ContentBlock.category_id == filters.category_id)

        if filters.is_published is not None:
            query = query.filter(ContentBlock.is_published == filters.is_published)

        if filters.tags:
            # Filtrar por tags (PostgreSQL JSON contains)
            for tag in filters.tags:
                query = query.filter(ContentBlock.tags.contains([tag]))

        # Total
        total = query.count()

        # Paginación
        blocks = query.order_by(ContentBlock.created_at.desc()).offset(filters.offset).limit(filters.page_size).all()

        return blocks, total

    @staticmethod
    def update_content_block(
        db: Session,
        block_id: int,
        tenant_id: int,
        data: schemas.ContentBlockUpdate
    ) -> ContentBlock:
        """Actualizar bloque de contenido"""
        block = ContentService.get_content_block(db, block_id, tenant_id)

        update_data = data.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(block, field, value)

        db.commit()
        db.refresh(block)

        return block

    @staticmethod
    def delete_content_block(db: Session, block_id: int, tenant_id: int) -> bool:
        """Soft delete de bloque"""
        block = ContentService.get_content_block(db, block_id, tenant_id)
        block.deleted_at = datetime.utcnow()
        db.commit()
        return True

    @staticmethod
    def search_content(db: Session, tenant_id: int, query: str) -> list[ContentBlock]:
        """
        Búsqueda de contenido por texto

        Busca en title, description y content_text
        """
        search_term = f"%{query}%"

        results = db.query(ContentBlock).filter(
            ContentBlock.tenant_id == tenant_id,
            ContentBlock.is_published == True,
            or_(
                ContentBlock.title.ilike(search_term),
                ContentBlock.description.ilike(search_term),
                ContentBlock.content_text.ilike(search_term)
            )
        ).limit(20).all()

        return results

    @staticmethod
    def duplicate_content_block(
        db: Session,
        block_id: int,
        tenant_id: int,
        new_title: str
    ) -> ContentBlock:
        """Duplicar bloque de contenido"""
        original = ContentService.get_content_block(db, block_id, tenant_id)

        new_block = ContentBlock(
            tenant_id=tenant_id,
            title=new_title,
            description=original.description,
            content_type=original.content_type,
            content_text=original.content_text,
            content_url=original.content_url,
            content_metadata=original.content_metadata.copy() if original.content_metadata else None,
            category_id=original.category_id,
            tags=original.tags.copy() if original.tags else [],
            is_published=False  # Duplicados empiezan como no publicados
        )

        db.add(new_block)
        db.commit()
        db.refresh(new_block)

        return new_block
```

## 4. Router (router.py)

### Content Endpoints

```python
from fastapi import APIRouter, Depends, status, UploadFile, File
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.schemas import SuccessResponse, PaginatedResponse
from app.core.enums import UserRole
from app.core.storage import storage_service
from app.core.exceptions import ValidationException
from app.content import schemas, service
from app.auth.dependencies import get_current_user, require_role
from app.tenants.models import Tenant
from app.tenants.dependencies import get_current_tenant
from app.users.models import User

router = APIRouter(prefix="/content", tags=["Content"])

# Categories

@router.post("/categories", response_model=schemas.ContentCategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
    data: schemas.ContentCategoryCreate,
    tenant: Tenant = Depends(get_current_tenant),
    current_user: User = Depends(require_role(UserRole.TENANT_ADMIN)),
    db: Session = Depends(get_db)
):
    """Crear categoría de contenido"""
    category = service.ContentService.create_category(db, tenant.id, data)
    return category

@router.get("/categories", response_model=list[schemas.ContentCategoryResponse])
async def list_categories(
    tenant: Tenant = Depends(get_current_tenant),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Listar categorías"""
    categories = service.ContentService.list_categories(db, tenant.id)
    return categories

# Content Blocks

@router.post("/blocks", response_model=schemas.ContentBlockResponse, status_code=status.HTTP_201_CREATED)
async def create_content_block(
    data: schemas.ContentBlockCreate,
    tenant: Tenant = Depends(get_current_tenant),
    current_user: User = Depends(require_role(UserRole.TENANT_ADMIN)),
    db: Session = Depends(get_db)
):
    """Crear bloque de contenido"""
    block = service.ContentService.create_content_block(db, tenant.id, data)
    return block

@router.get("/blocks", response_model=PaginatedResponse[schemas.ContentBlockListResponse])
async def list_content_blocks(
    filters: schemas.ContentFilterParams = Depends(),
    tenant: Tenant = Depends(get_current_tenant),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Listar bloques de contenido"""
    blocks, total = service.ContentService.list_content_blocks(db, tenant.id, filters)

    return PaginatedResponse(
        data=blocks,
        total=total,
        page=filters.page,
        page_size=filters.page_size,
        total_pages=(total + filters.page_size - 1) // filters.page_size
    )

@router.get("/blocks/{block_id}", response_model=schemas.ContentBlockResponse)
async def get_content_block(
    block_id: int,
    tenant: Tenant = Depends(get_current_tenant),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener bloque por ID"""
    block = service.ContentService.get_content_block(db, block_id, tenant.id)
    return block

@router.patch("/blocks/{block_id}", response_model=schemas.ContentBlockResponse)
async def update_content_block(
    block_id: int,
    data: schemas.ContentBlockUpdate,
    tenant: Tenant = Depends(get_current_tenant),
    current_user: User = Depends(require_role(UserRole.TENANT_ADMIN)),
    db: Session = Depends(get_db)
):
    """Actualizar bloque"""
    block = service.ContentService.update_content_block(db, block_id, tenant.id, data)
    return block

@router.delete("/blocks/{block_id}", response_model=SuccessResponse)
async def delete_content_block(
    block_id: int,
    tenant: Tenant = Depends(get_current_tenant),
    current_user: User = Depends(require_role(UserRole.TENANT_ADMIN)),
    db: Session = Depends(get_db)
):
    """Eliminar bloque"""
    service.ContentService.delete_content_block(db, block_id, tenant.id)
    return SuccessResponse(message="Bloque eliminado exitosamente")

@router.post("/blocks/{block_id}/duplicate", response_model=schemas.ContentBlockResponse)
async def duplicate_content_block(
    block_id: int,
    new_title: str,
    tenant: Tenant = Depends(get_current_tenant),
    current_user: User = Depends(require_role(UserRole.TENANT_ADMIN)),
    db: Session = Depends(get_db)
):
    """Duplicar bloque"""
    block = service.ContentService.duplicate_content_block(db, block_id, tenant.id, new_title)
    return block

# File Uploads

@router.post("/upload", response_model=schemas.FileUploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    tenant: Tenant = Depends(get_current_tenant),
    current_user: User = Depends(require_role(UserRole.TENANT_ADMIN)),
    db: Session = Depends(get_db)
):
    """
    Subir archivo (imagen, PDF, etc.)

    - Max 10MB
    - Formatos: PNG, JPG, PDF, MP4
    """
    # Validar tamaño
    file_data = await file.read()
    size_bytes = len(file_data)

    if size_bytes > 10 * 1024 * 1024:  # 10MB
        raise ValidationException("Archivo muy grande. Máximo 10MB")

    # Validar tipo
    allowed_types = [
        "image/png", "image/jpeg", "image/gif",
        "application/pdf",
        "video/mp4", "video/webm"
    ]

    if file.content_type not in allowed_types:
        raise ValidationException("Formato no permitido")

    # Subir
    filename = f"{file.filename}"
    url = await storage_service.upload_file(
        file_data,
        filename,
        folder=f"tenants/{tenant.id}/content",
        content_type=file.content_type
    )

    # Metadata según tipo
    metadata = {
        "size_bytes": size_bytes,
        "original_filename": file.filename
    }

    return {
        "url": url,
        "content_type": file.content_type,
        "size_bytes": size_bytes,
        "metadata": metadata
    }

# Search

@router.get("/search", response_model=list[schemas.ContentBlockListResponse])
async def search_content(
    q: str,
    tenant: Tenant = Depends(get_current_tenant),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Buscar contenido"""
    results = service.ContentService.search_content(db, tenant.id, q)
    return results
```

## Dependencias entre Módulos

**Depende de:**
- Core (storage, database)
- Tenants (tenant_id)

**Es usado por:**
- Onboarding (módulos pueden referenciar ContentBlock)

## Testing

Tests de CRUD, upload, búsqueda y categorización.

## Checklist

- [ ] Modelos ContentBlock y ContentCategory
- [ ] CRUD completo
- [ ] Upload de archivos
- [ ] Sistema de categorías y tags
- [ ] Búsqueda de contenido
- [ ] Tests 80%+

## Notas

1. Implementar después de Core y Tenants
2. Integrar con storage (S3/Cloudinary)
3. Validar tipos de archivo y tamaños

## Dependencias

Ninguna adicional.
