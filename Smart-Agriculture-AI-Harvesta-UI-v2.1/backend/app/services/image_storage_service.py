"""
Image Storage Service for Crop Disease Scans.
Handles safe image validation, size checks, MIME verification, UUID naming,
and local disk storage (with forward compatibility for Supabase Storage).
"""

import io
import os
import uuid
import logging
from typing import Tuple, Optional
from urllib import error, request
from urllib.parse import quote
from PIL import Image

logger = logging.getLogger(__name__)

# Constants
MAX_IMAGE_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB
ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/webp", "image/jpg"}
ALLOWED_PIL_FORMATS = {"JPEG", "PNG", "WEBP"}

WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
LOCAL_UPLOAD_DIR = os.path.abspath(
    os.getenv("DISEASE_UPLOAD_DIR", os.path.join(WORKSPACE_ROOT, "data", "uploads", "disease_scans"))
)


class ImageStorageService:
    @staticmethod
    def _cloud_config():
        enabled = os.getenv("SUPABASE_STORAGE_ENABLED", "false").strip().lower() == "true"
        url = os.getenv("SUPABASE_URL", "").strip().rstrip("/")
        # Prefer Supabase's current sb_secret_* server key. Keep the legacy
        # service_role variable as a transition fallback for older projects.
        service_key = (
            os.getenv("SUPABASE_SECRET_KEY", "").strip()
            or os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()
        )
        bucket = os.getenv("SUPABASE_STORAGE_BUCKET", "crop-disease-scans").strip()
        return enabled and bool(url and service_key and bucket), url, service_key, bucket

    @staticmethod
    def _cloud_auth_headers(service_key: str):
        """Build headers compatible with current and legacy Supabase keys."""
        headers = {"apikey": service_key}
        # Modern sb_secret_* keys are API keys, not JWTs, and must not be sent
        # as bearer tokens. Legacy service_role values are JWTs and still need
        # the Authorization header for Storage's RLS bypass.
        if not service_key.startswith("sb_secret_"):
            headers["Authorization"] = f"Bearer {service_key}"
        return headers

    @staticmethod
    def _jpeg_bytes(image: Image.Image) -> bytes:
        output = io.BytesIO()
        image.convert("RGB").save(output, "JPEG", quality=90, optimize=True)
        return output.getvalue()

    @classmethod
    def _upload_to_supabase(cls, jpeg_bytes: bytes, object_path: str) -> Optional[str]:
        enabled, url, service_key, bucket = cls._cloud_config()
        if not enabled:
            return None

        endpoint = f"{url}/storage/v1/object/{quote(bucket)}/{quote(object_path, safe='/')}"
        headers = cls._cloud_auth_headers(service_key)
        headers.update({
            "Content-Type": "image/jpeg",
            "x-upsert": "false",
        })
        req = request.Request(
            endpoint,
            data=jpeg_bytes,
            headers=headers,
            method="POST",
        )
        try:
            with request.urlopen(req, timeout=30):
                pass
            return f"supabase://{bucket}/{object_path}"
        except Exception as exc:
            logger.error("Supabase Storage upload failed; using local storage: %s", exc)
            if os.getenv("SUPABASE_STORAGE_REQUIRED", "false").strip().lower() == "true":
                raise RuntimeError("Supabase Storage upload failed.") from exc
            return None

    @staticmethod
    def _parse_supabase_key(storage_key: str):
        if not storage_key or not storage_key.startswith("supabase://"):
            return None
        remainder = storage_key[len("supabase://"):]
        if "/" not in remainder:
            return None
        bucket, object_path = remainder.split("/", 1)
        return bucket, object_path

    @staticmethod
    def ensure_upload_dir() -> str:
        """Ensures that the upload directory exists on the local filesystem."""
        os.makedirs(LOCAL_UPLOAD_DIR, exist_ok=True)
        return LOCAL_UPLOAD_DIR

    @classmethod
    def validate_and_process_image(cls, file_bytes: bytes, filename: str, content_type: Optional[str] = None) -> Tuple[Image.Image, str]:
        """
        Performs strict security checks on uploaded image bytes:
        - Rejects empty uploads
        - Enforces size limit (<= 5MB)
        - Verifies content type / extension
        - Validates Pillow image decoding integrity
        Returns (PIL.Image, sanitized_format).
        """
        if not file_bytes or len(file_bytes) == 0:
            raise ValueError("Uploaded image file is empty.")

        if len(file_bytes) > MAX_IMAGE_SIZE_BYTES:
            size_mb = len(file_bytes) / (1024 * 1024)
            raise ValueError(f"Image file size ({size_mb:.2f} MB) exceeds the 5.0 MB maximum limit.")

        # Check content type if provided
        if content_type and content_type.lower() not in ALLOWED_MIME_TYPES:
            raise ValueError(f"Unsupported image MIME type '{content_type}'. Allowed types: JPEG, PNG, WebP.")

        try:
            image = Image.open(io.BytesIO(file_bytes))
            image.verify()  # Verifies file integrity without decoding entire image yet
            
            # Reopen for actual conversion/processing because verify() closes the stream
            image = Image.open(io.BytesIO(file_bytes))
            img_format = (image.format or "JPEG").upper()

            if img_format not in ALLOWED_PIL_FORMATS:
                raise ValueError(f"Unsupported image format '{img_format}'. Supported formats: JPEG, PNG, WebP.")

            return image, img_format.lower()
        except Exception as e:
            if isinstance(e, ValueError):
                raise
            logger.warning(f"Corrupted image upload rejected: {e}")
            raise ValueError("Corrupted or unreadable image file. Please upload a valid JPEG, PNG, or WebP photo.")

    @classmethod
    def save_scan_image(
        cls,
        file_bytes: bytes,
        filename: str,
        content_type: Optional[str] = None,
        owner_id: Optional[int] = None,
    ) -> Tuple[str, Image.Image]:
        """
        Validates, converts to standard RGB JPEG, saves to local upload directory,
        and returns (storage_path_key, PIL.Image).
        """
        image, _ = cls.validate_and_process_image(file_bytes, filename, content_type)
        # Generate secure random filename
        unique_name = f"scan_{uuid.uuid4().hex[:16]}.jpg"
        rgb_image = image.convert("RGB")
        jpeg_bytes = cls._jpeg_bytes(rgb_image)

        # Production path: private Supabase Storage object, grouped by user.
        cloud_path = f"users/{owner_id or 'unassigned'}/disease-scans/{unique_name}"
        cloud_key = cls._upload_to_supabase(jpeg_bytes, cloud_path)
        if cloud_key:
            return cloud_key, rgb_image

        # Local development fallback.
        cls.ensure_upload_dir()
        target_path = os.path.join(LOCAL_UPLOAD_DIR, unique_name)
        with open(target_path, "wb") as output:
            output.write(jpeg_bytes)

        # Relative path / storage key stored in DB
        storage_key = f"uploads/disease_scans/{unique_name}"
        return storage_key, rgb_image

    @classmethod
    def get_absolute_image_path(cls, storage_key: str) -> Optional[str]:
        """
        Resolves storage key to absolute local filepath with directory traversal guards.
        """
        if not storage_key or storage_key.startswith("supabase://"):
            return None

        clean_name = os.path.basename(storage_key)
        abs_path = os.path.abspath(os.path.join(LOCAL_UPLOAD_DIR, clean_name))

        # Traversal protection
        if not abs_path.startswith(os.path.abspath(LOCAL_UPLOAD_DIR)):
            logger.warning(f"Potential directory traversal attempt blocked: {storage_key}")
            return None

        if os.path.exists(abs_path):
            return abs_path
        return None

    @classmethod
    def delete_scan_image(cls, storage_key: str) -> bool:
        """
        Safely removes stored scan image from disk.
        """
        cloud_parts = cls._parse_supabase_key(storage_key)
        if cloud_parts:
            bucket, object_path = cloud_parts
            enabled, url, service_key, _ = cls._cloud_config()
            if not enabled:
                logger.error("Supabase Storage key cannot be deleted because cloud storage is not configured.")
                return False
            endpoint = f"{url}/storage/v1/object/{quote(bucket)}/{quote(object_path, safe='/')}"
            req = request.Request(
                endpoint,
                headers=cls._cloud_auth_headers(service_key),
                method="DELETE",
            )
            try:
                with request.urlopen(req, timeout=30):
                    pass
                return True
            except Exception as exc:
                logger.error("Failed to delete Supabase Storage object: %s", exc)
                return False

        abs_path = cls.get_absolute_image_path(storage_key)
        if abs_path and os.path.exists(abs_path):
            try:
                os.remove(abs_path)
                return True
            except Exception as e:
                logger.error(f"Failed to delete scan image {abs_path}: {e}")
        return False

    @classmethod
    def get_scan_image_bytes(cls, storage_key: str) -> Optional[bytes]:
        """Returns image bytes from private Supabase Storage or local disk."""
        cloud_parts = cls._parse_supabase_key(storage_key)
        if cloud_parts:
            bucket, object_path = cloud_parts
            enabled, url, service_key, _ = cls._cloud_config()
            if not enabled:
                return None
            endpoint = f"{url}/storage/v1/object/{quote(bucket)}/{quote(object_path, safe='/')}"
            req = request.Request(
                endpoint,
                headers=cls._cloud_auth_headers(service_key),
                method="GET",
            )
            try:
                with request.urlopen(req, timeout=30) as response:
                    return response.read()
            except (error.URLError, error.HTTPError, TimeoutError) as exc:
                logger.error("Failed to download Supabase Storage object: %s", exc)
                return None

        abs_path = cls.get_absolute_image_path(storage_key)
        if not abs_path:
            return None
        try:
            with open(abs_path, "rb") as source:
                return source.read()
        except OSError:
            return None
