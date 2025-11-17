"""
File storage service abstraction.
Supports both AWS S3 and Cloudinary for file uploads.
"""

import io
from typing import BinaryIO
import boto3
from botocore.exceptions import ClientError
import cloudinary
import cloudinary.uploader
from app.core.config import settings
from app.core.exceptions import FileUploadException
from app.core.utils import generate_unique_filename, sanitize_filename


class StorageService:
    """
    Abstraction layer for file storage.
    Automatically uses Cloudinary if configured, otherwise falls back to AWS S3.
    """

    def __init__(self):
        """Initialize storage service with appropriate backend."""
        self.use_cloudinary = bool(settings.CLOUDINARY_CLOUD_NAME)

        if self.use_cloudinary:
            self._init_cloudinary()
        else:
            self._init_s3()

    def _init_cloudinary(self) -> None:
        """Initialize Cloudinary configuration."""
        cloudinary.config(
            cloud_name=settings.CLOUDINARY_CLOUD_NAME,
            api_key=settings.CLOUDINARY_API_KEY,
            api_secret=settings.CLOUDINARY_API_SECRET,
            secure=True
        )

    def _init_s3(self) -> None:
        """Initialize AWS S3 client."""
        if not settings.AWS_ACCESS_KEY_ID or not settings.AWS_SECRET_ACCESS_KEY:
            # S3 not configured, storage operations will fail
            self.s3_client = None
            return

        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION
        )

    async def upload_file(
        self,
        file_data: bytes | BinaryIO,
        filename: str,
        folder: str = "uploads",
        content_type: str | None = None,
        make_unique: bool = True
    ) -> str:
        """
        Upload file to storage and return public URL.

        Args:
            file_data: File bytes or file-like object
            filename: Original filename
            folder: Folder/prefix for organization
            content_type: MIME type of the file
            make_unique: Whether to generate unique filename (default: True)

        Returns:
            Public URL of the uploaded file

        Raises:
            FileUploadException: If upload fails

        Example:
            >>> url = await storage_service.upload_file(
            ...     file_data=image_bytes,
            ...     filename="profile.jpg",
            ...     folder="avatars",
            ...     content_type="image/jpeg"
            ... )
        """
        # Sanitize and optionally make filename unique
        if make_unique:
            filename = generate_unique_filename(filename)
        else:
            filename = sanitize_filename(filename)

        if self.use_cloudinary:
            return await self._upload_cloudinary(file_data, filename, folder)
        else:
            return await self._upload_s3(file_data, filename, folder, content_type)

    async def _upload_s3(
        self,
        file_data: bytes | BinaryIO,
        filename: str,
        folder: str,
        content_type: str | None
    ) -> str:
        """
        Upload file to AWS S3.

        Args:
            file_data: File bytes or file-like object
            filename: Filename to use
            folder: S3 prefix/folder
            content_type: MIME type

        Returns:
            Public URL of uploaded file

        Raises:
            FileUploadException: If S3 upload fails
        """
        if not self.s3_client:
            raise FileUploadException("AWS S3 no está configurado")

        if not settings.AWS_BUCKET_NAME:
            raise FileUploadException("AWS S3 bucket no está configurado")

        # Construct S3 key (path)
        key = f"{folder}/{filename}"

        # Convert to bytes if file-like object
        if not isinstance(file_data, bytes):
            file_data = file_data.read()

        try:
            # Upload to S3
            self.s3_client.put_object(
                Bucket=settings.AWS_BUCKET_NAME,
                Key=key,
                Body=file_data,
                ContentType=content_type or 'application/octet-stream',
                ACL='public-read'  # Make file publicly accessible
            )

            # Construct public URL
            url = f"https://{settings.AWS_BUCKET_NAME}.s3.{settings.AWS_REGION}.amazonaws.com/{key}"
            return url

        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            raise FileUploadException(f"Error al subir a S3: {error_code}")

        except Exception as e:
            raise FileUploadException(f"Error inesperado al subir a S3: {str(e)}")

    async def _upload_cloudinary(
        self,
        file_data: bytes | BinaryIO,
        filename: str,
        folder: str
    ) -> str:
        """
        Upload file to Cloudinary.

        Args:
            file_data: File bytes or file-like object
            filename: Filename to use
            folder: Cloudinary folder

        Returns:
            Public URL of uploaded file

        Raises:
            FileUploadException: If Cloudinary upload fails
        """
        try:
            # Remove file extension for public_id (Cloudinary adds it automatically)
            public_id = filename.rsplit('.', 1)[0] if '.' in filename else filename

            # Upload to Cloudinary
            result = cloudinary.uploader.upload(
                file_data,
                folder=folder,
                public_id=public_id,
                resource_type='auto'  # Auto-detect resource type (image, video, raw)
            )

            return result['secure_url']

        except Exception as e:
            raise FileUploadException(f"Error al subir a Cloudinary: {str(e)}")

    async def delete_file(self, url: str) -> bool:
        """
        Delete file from storage.

        Args:
            url: Public URL of the file to delete

        Returns:
            True if deletion was successful, False otherwise

        Example:
            >>> success = await storage_service.delete_file(file_url)
        """
        if self.use_cloudinary:
            return await self._delete_cloudinary(url)
        else:
            return await self._delete_s3(url)

    async def _delete_s3(self, url: str) -> bool:
        """
        Delete file from AWS S3.

        Args:
            url: S3 file URL

        Returns:
            True if successful, False otherwise
        """
        if not self.s3_client or not settings.AWS_BUCKET_NAME:
            return False

        try:
            # Extract key from URL
            # URL format: https://bucket.s3.region.amazonaws.com/folder/filename
            parts = url.split('.amazonaws.com/')
            if len(parts) != 2:
                return False

            key = parts[1]

            # Delete from S3
            self.s3_client.delete_object(
                Bucket=settings.AWS_BUCKET_NAME,
                Key=key
            )

            return True

        except Exception:
            return False

    async def _delete_cloudinary(self, url: str) -> bool:
        """
        Delete file from Cloudinary.

        Args:
            url: Cloudinary file URL

        Returns:
            True if successful, False otherwise
        """
        try:
            # Extract public_id from URL
            # Cloudinary URLs contain version number and public_id
            # Format: https://res.cloudinary.com/cloud/resource_type/upload/v123456/folder/filename.ext

            # This is a simplified extraction - may need adjustment based on actual URLs
            parts = url.split('/upload/')
            if len(parts) != 2:
                return False

            # Get everything after 'upload/'
            path_with_version = parts[1]

            # Remove version (vXXXXXXX/)
            import re
            path = re.sub(r'^v\d+/', '', path_with_version)

            # Remove file extension for public_id
            public_id = path.rsplit('.', 1)[0]

            # Delete from Cloudinary
            cloudinary.uploader.destroy(public_id)

            return True

        except Exception:
            return False

    def get_upload_url(self, key: str) -> str:
        """
        Generate a presigned URL for direct upload (S3 only).

        Args:
            key: S3 key (path) for the file

        Returns:
            Presigned upload URL

        Raises:
            FileUploadException: If S3 is not configured or operation fails
        """
        if self.use_cloudinary:
            raise FileUploadException("Presigned URLs solo están disponibles con S3")

        if not self.s3_client or not settings.AWS_BUCKET_NAME:
            raise FileUploadException("AWS S3 no está configurado")

        try:
            url = self.s3_client.generate_presigned_url(
                'put_object',
                Params={
                    'Bucket': settings.AWS_BUCKET_NAME,
                    'Key': key
                },
                ExpiresIn=3600  # 1 hour
            )
            return url

        except Exception as e:
            raise FileUploadException(f"Error al generar URL de subida: {str(e)}")


# Singleton instance
storage_service = StorageService()
