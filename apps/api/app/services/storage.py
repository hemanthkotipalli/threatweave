from __future__ import annotations

import os
import uuid
from typing import Protocol

from app.core.config import settings


class StorageService(Protocol):
    """
    Protocol definition for file storage service.
    This enables swapability of S3 or local adapters in downstream components.
    """
    def save(self, file_bytes: bytes, filename: str, investigation_id: str | uuid.UUID, modality: str) -> str:
        """
        Saves file bytes to storage bucket/folder and returns a relative file path.
        """
        ...


class LocalStorageService:
    """
    Local filesystem storage implementation.
    Writes raw evidence files under STORAGE_PATH/investigation_id/modality_uuid.ext.
    """
    def __init__(self, storage_path: str | None = None) -> None:
        self.storage_path = storage_path or settings.STORAGE_PATH

    def save(self, file_bytes: bytes, filename: str, investigation_id: str | uuid.UUID, modality: str) -> str:
        """
        Saves file bytes to the local filesystem.
        Creates subdirectories idempotently and returns the relative path representation.
        """
        # Exclude directories and clean filename
        _, ext = os.path.splitext(filename)
        ext = ext.lower()
        
        # Build storage sub-folder path
        folder_name = str(investigation_id)
        target_dir = os.path.join(self.storage_path, folder_name)
        os.makedirs(target_dir, exist_ok=True)

        # Generate unique file identifier
        unique_id = uuid.uuid4().hex
        generated_filename = f"{modality}_{unique_id}{ext}"
        
        # Write bytes locally
        target_file_path = os.path.join(target_dir, generated_filename)
        with open(target_file_path, "wb") as f:
            f.write(file_bytes)

        # Return relative storage path for DB row
        return f"{folder_name}/{generated_filename}"
