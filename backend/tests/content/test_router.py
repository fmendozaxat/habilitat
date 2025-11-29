"""
Tests for content router endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.users.models import User
from app.tenants.models import Tenant
from app.content.models import ContentBlock, ContentCategory


def create_test_tenant(db: Session) -> Tenant:
    """Helper to create a test tenant."""
    tenant = Tenant(name="Test Tenant", slug="test-tenant", plan="professional")
    db.add(tenant)
    db.commit()
    db.refresh(tenant)
    return tenant


def create_test_admin(db: Session, tenant_id: int) -> User:
    """Helper to create a test admin."""
    admin = User(
        email="admin@example.com",
        hashed_password=get_password_hash("TestPassword123!"),
        first_name="Admin",
        last_name="User",
        tenant_id=tenant_id,
        role="tenant_admin",
        is_active=True
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    return admin


def get_auth_token(client: TestClient, email: str) -> str:
    """Helper to get authentication token."""
    response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "TestPassword123!"}
    )
    return response.json()["access_token"]


class TestContentBlockCRUD:
    """Tests for content block CRUD operations."""

    def test_create_content_block(self, client: TestClient, db: Session):
        """Test creating a content block."""
        tenant = create_test_tenant(db)
        admin = create_test_admin(db, tenant.id)
        token = get_auth_token(client, admin.email)

        response = client.post(
            "/api/v1/content/blocks",
            headers={
                "Authorization": f"Bearer {token}",
                "X-Tenant-ID": str(tenant.id)
            },
            json={
                "title": "Welcome Message",
                "block_type": "text",
                "content": {"text": "Welcome to our company!"},
                "is_active": True
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Welcome Message"
        assert data["block_type"] == "text"

    def test_list_content_blocks(self, client: TestClient, db: Session):
        """Test listing content blocks."""
        tenant = create_test_tenant(db)
        admin = create_test_admin(db, tenant.id)

        # Create some content blocks
        for i in range(3):
            block = ContentBlock(
                tenant_id=tenant.id,
                title=f"Block {i}",
                block_type="text",
                content={"text": f"Content {i}"},
                is_active=True
            )
            db.add(block)
        db.commit()

        token = get_auth_token(client, admin.email)

        response = client.get(
            "/api/v1/content/blocks",
            headers={
                "Authorization": f"Bearer {token}",
                "X-Tenant-ID": str(tenant.id)
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 3

    def test_get_content_block(self, client: TestClient, db: Session):
        """Test getting a specific content block."""
        tenant = create_test_tenant(db)
        admin = create_test_admin(db, tenant.id)

        block = ContentBlock(
            tenant_id=tenant.id,
            title="Test Block",
            block_type="video",
            content={"url": "https://example.com/video.mp4"},
            is_active=True
        )
        db.add(block)
        db.commit()

        token = get_auth_token(client, admin.email)

        response = client.get(
            f"/api/v1/content/blocks/{block.id}",
            headers={
                "Authorization": f"Bearer {token}",
                "X-Tenant-ID": str(tenant.id)
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == block.id
        assert data["title"] == "Test Block"

    def test_update_content_block(self, client: TestClient, db: Session):
        """Test updating a content block."""
        tenant = create_test_tenant(db)
        admin = create_test_admin(db, tenant.id)

        block = ContentBlock(
            tenant_id=tenant.id,
            title="Original Title",
            block_type="text",
            content={"text": "Original content"},
            is_active=True
        )
        db.add(block)
        db.commit()

        token = get_auth_token(client, admin.email)

        response = client.patch(
            f"/api/v1/content/blocks/{block.id}",
            headers={
                "Authorization": f"Bearer {token}",
                "X-Tenant-ID": str(tenant.id)
            },
            json={"title": "Updated Title"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Title"

    def test_delete_content_block(self, client: TestClient, db: Session):
        """Test deleting a content block."""
        tenant = create_test_tenant(db)
        admin = create_test_admin(db, tenant.id)

        block = ContentBlock(
            tenant_id=tenant.id,
            title="Delete Me",
            block_type="text",
            content={"text": "To be deleted"},
            is_active=True
        )
        db.add(block)
        db.commit()

        token = get_auth_token(client, admin.email)

        response = client.delete(
            f"/api/v1/content/blocks/{block.id}",
            headers={
                "Authorization": f"Bearer {token}",
                "X-Tenant-ID": str(tenant.id)
            }
        )

        assert response.status_code == 200

        # Verify soft delete
        db.refresh(block)
        assert block.deleted_at is not None

    def test_cannot_access_other_tenant_content(self, client: TestClient, db: Session):
        """Test that content from other tenants is not accessible."""
        tenant1 = Tenant(name="Tenant 1", slug="tenant-1", plan="professional")
        tenant2 = Tenant(name="Tenant 2", slug="tenant-2", plan="professional")
        db.add_all([tenant1, tenant2])
        db.commit()

        admin1 = create_test_admin(db, tenant1.id)

        # Create content in tenant2
        block = ContentBlock(
            tenant_id=tenant2.id,
            title="Tenant 2 Block",
            block_type="text",
            content={"text": "Private content"},
            is_active=True
        )
        db.add(block)
        db.commit()

        token = get_auth_token(client, admin1.email)

        # Try to access from tenant1
        response = client.get(
            f"/api/v1/content/blocks/{block.id}",
            headers={
                "Authorization": f"Bearer {token}",
                "X-Tenant-ID": str(tenant1.id)
            }
        )

        assert response.status_code == 404


class TestContentCategories:
    """Tests for content category operations."""

    def test_create_category(self, client: TestClient, db: Session):
        """Test creating a content category."""
        tenant = create_test_tenant(db)
        admin = create_test_admin(db, tenant.id)
        token = get_auth_token(client, admin.email)

        response = client.post(
            "/api/v1/content/categories",
            headers={
                "Authorization": f"Bearer {token}",
                "X-Tenant-ID": str(tenant.id)
            },
            json={
                "name": "Training Videos",
                "description": "All training video content"
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Training Videos"

    def test_list_categories(self, client: TestClient, db: Session):
        """Test listing content categories."""
        tenant = create_test_tenant(db)
        admin = create_test_admin(db, tenant.id)

        # Create categories
        for name in ["Videos", "Documents", "Quizzes"]:
            cat = ContentCategory(tenant_id=tenant.id, name=name)
            db.add(cat)
        db.commit()

        token = get_auth_token(client, admin.email)

        response = client.get(
            "/api/v1/content/categories",
            headers={
                "Authorization": f"Bearer {token}",
                "X-Tenant-ID": str(tenant.id)
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 3


class TestContentSearch:
    """Tests for content search functionality."""

    def test_search_content_by_title(self, client: TestClient, db: Session):
        """Test searching content by title."""
        tenant = create_test_tenant(db)
        admin = create_test_admin(db, tenant.id)

        # Create content with different titles
        blocks = [
            ContentBlock(tenant_id=tenant.id, title="Python Basics", block_type="text", content={}),
            ContentBlock(tenant_id=tenant.id, title="Python Advanced", block_type="text", content={}),
            ContentBlock(tenant_id=tenant.id, title="JavaScript Intro", block_type="text", content={}),
        ]
        for block in blocks:
            block.is_active = True
        db.add_all(blocks)
        db.commit()

        token = get_auth_token(client, admin.email)

        response = client.get(
            "/api/v1/content/blocks?search=Python",
            headers={
                "Authorization": f"Bearer {token}",
                "X-Tenant-ID": str(tenant.id)
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 2
        for item in data["items"]:
            assert "Python" in item["title"]

    def test_filter_content_by_type(self, client: TestClient, db: Session):
        """Test filtering content by type."""
        tenant = create_test_tenant(db)
        admin = create_test_admin(db, tenant.id)

        # Create content with different types
        blocks = [
            ContentBlock(tenant_id=tenant.id, title="Video 1", block_type="video", content={}, is_active=True),
            ContentBlock(tenant_id=tenant.id, title="Video 2", block_type="video", content={}, is_active=True),
            ContentBlock(tenant_id=tenant.id, title="Text 1", block_type="text", content={}, is_active=True),
        ]
        db.add_all(blocks)
        db.commit()

        token = get_auth_token(client, admin.email)

        response = client.get(
            "/api/v1/content/blocks?block_type=video",
            headers={
                "Authorization": f"Bearer {token}",
                "X-Tenant-ID": str(tenant.id)
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 2
        for item in data["items"]:
            assert item["block_type"] == "video"
