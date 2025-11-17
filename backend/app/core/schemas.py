"""
Base Pydantic schemas for request/response validation.
Provides common schemas for pagination, responses, and base classes.
"""

from typing import Generic, TypeVar, List
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class BaseSchema(BaseModel):
    """
    Base schema for all Pydantic models.
    Enables ORM mode for SQLAlchemy model conversion.
    """

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True
    )


class TimestampSchema(BaseSchema):
    """Schema that includes timestamp fields."""

    created_at: datetime
    updated_at: datetime


class PaginationParams(BaseModel):
    """
    Query parameters for pagination.

    Attributes:
        page: Page number (1-indexed)
        page_size: Number of items per page
    """

    page: int = Field(default=1, ge=1, description="Page number")
    page_size: int = Field(
        default=20,
        ge=1,
        le=100,
        description="Number of items per page"
    )

    @property
    def offset(self) -> int:
        """Calculate offset for database query."""
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        """Return limit for database query."""
        return self.page_size


# Type variable for generic pagination
DataT = TypeVar('DataT')


class PaginatedResponse(BaseModel, Generic[DataT]):
    """
    Generic paginated response.

    Attributes:
        data: List of items
        total: Total number of items
        page: Current page number
        page_size: Items per page
        total_pages: Total number of pages
    """

    data: List[DataT]
    total: int = Field(description="Total number of items")
    page: int = Field(description="Current page number")
    page_size: int = Field(description="Number of items per page")
    total_pages: int = Field(description="Total number of pages")

    @staticmethod
    def create(
        data: List[DataT],
        total: int,
        page: int,
        page_size: int
    ) -> "PaginatedResponse[DataT]":
        """
        Factory method to create a paginated response.

        Args:
            data: List of items for current page
            total: Total number of items
            page: Current page number
            page_size: Items per page

        Returns:
            PaginatedResponse instance
        """
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0

        return PaginatedResponse(
            data=data,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )


class SuccessResponse(BaseModel):
    """
    Standard success response.

    Attributes:
        success: Always True
        message: Success message
    """

    success: bool = True
    message: str


class ErrorResponse(BaseModel):
    """
    Standard error response.

    Attributes:
        success: Always False
        error: Error type or title
        detail: Detailed error message
    """

    success: bool = False
    error: str
    detail: str | None = None


class MessageResponse(BaseModel):
    """
    Simple message response.

    Attributes:
        message: Response message
    """

    message: str


class IDResponse(BaseModel):
    """
    Response containing only an ID.

    Attributes:
        id: Resource ID
    """

    id: int
