from __future__ import annotations

import logging
import uuid

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.core.errors import AuthenticationError, ValidationError
from app.core.file_validation import (
    validate_audio_file,
    validate_image_file,
    validate_text_length,
)
from app.models.enums import Modality
from app.models.evidence_input import EvidenceInput
from app.models.investigation import Investigation
from app.models.user import User
from app.services.storage import LocalStorageService

logger = logging.getLogger("threatweave-api.ingestion")


def ingest_investigation(
    db: Session,
    title: str | None = None,
    text: str | None = None,
    url: str | None = None,
    image_file: UploadFile | None = None,
    voice_file: UploadFile | None = None,
    storage_service: LocalStorageService | None = None,
    user_id: uuid.UUID | None = None,
    is_demo: bool = False,
) -> Investigation:
    """
    Ingests and processes raw multimodal evidence inputs for a new investigation task.
    Executes entirely within an atomic database transaction block.

    1. Validates that at least one evidence source is present.
    2. Validates sizes and binary magic byte signatures.
    3. Persists files to disk via StorageService.
    4. Attributes investigation to the authenticated user (or system_analyst for demo mode).
    5. Creates db rows for Investigation and EvidenceInputs.
    """
    # 1. Validate that at least one modality is provided
    has_text = text is not None and len(text.strip()) > 0
    has_url = url is not None and len(url.strip()) > 0
    has_image = image_file is not None
    has_voice = voice_file is not None

    if not (has_text or has_url or has_image or has_voice):
        logger.warning("Ingestion rejected: no evidence input provided")
        raise ValidationError(
            message="At least one evidence input (text, url, image, or voice) must be provided.",
            code="validation_error"
        )

    # Instantiate storage service if not provided
    storage = storage_service or LocalStorageService()

    # Pre-read and validate files to prevent partial uploads/transactions
    image_bytes = None
    voice_bytes = None

    if has_image and image_file:
        image_bytes = image_file.file.read()
        validate_image_file(image_bytes, image_file.filename or "image.png")

    if has_voice and voice_file:
        voice_bytes = voice_file.file.read()
        validate_audio_file(voice_bytes, voice_file.filename or "audio.mp3")

    if has_text and text:
        validate_text_length(text)

    # 2. Database transaction scope
    # Note: We rely on the db session's transaction management
    try:
        resolved_user_id: uuid.UUID
        if is_demo:
            # Curated Demo Mode scenarios stay open without login requirements.
            # Demo-created investigations are explicitly attributed to system_analyst.
            demo_user = db.query(User).filter(User.email == "system_analyst@threatweave.local").first()
            if not demo_user:
                demo_user = User(
                    email="system_analyst@threatweave.local",
                    password_hash="placeholder_demo_analyst_hash",
                    role="analyst",
                )
                db.add(demo_user)
                db.flush()
            resolved_user_id = demo_user.id
        else:
            # Real non-demo investigations MUST be attributed to an authenticated user.
            # The Phase 4 system_analyst auto-creation workaround has been removed here.
            if user_id is None:
                logger.warning("Ingestion rejected: user_id is missing for non-demo investigation")
                raise AuthenticationError(
                    message="User authentication is required to create an investigation.",
                    code="authentication_required",
                )
            target_user = db.query(User).filter(User.id == user_id).first()
            if not target_user:
                logger.warning("Ingestion rejected: user %s not found", user_id)
                raise AuthenticationError(
                    message="Authenticated user account was not found in the database.",
                    code="user_not_found",
                )
            resolved_user_id = target_user.id

        # Create new investigation row
        resolved_title = title.strip() if (title and title.strip()) else "Untitled investigation"
        investigation = Investigation(
            title=resolved_title,
            status="pending",
            user_id=resolved_user_id,
        )
        db.add(investigation)
        db.flush()  # Flush to generate investigation.id


        # 3. Create EvidenceInput records
        if has_text and text:
            input_text = EvidenceInput(
                investigation_id=investigation.id,
                modality=Modality.TEXT.value,
                raw_content_ref=text
            )
            db.add(input_text)

        if has_url and url:
            input_url = EvidenceInput(
                investigation_id=investigation.id,
                modality=Modality.URL.value,
                raw_content_ref=url
            )
            db.add(input_url)

        if has_image and image_file and image_bytes is not None:
            # Save to storage
            filename = image_file.filename or "image.png"
            file_path = storage.save(
                file_bytes=image_bytes,
                filename=filename,
                investigation_id=investigation.id,
                modality="image"
            )
            input_image = EvidenceInput(
                investigation_id=investigation.id,
                modality=Modality.IMAGE.value,
                file_path=file_path
            )
            db.add(input_image)

        if has_voice and voice_file and voice_bytes is not None:
            # Save to storage
            filename = voice_file.filename or "audio.mp3"
            file_path = storage.save(
                file_bytes=voice_bytes,
                filename=filename,
                investigation_id=investigation.id,
                modality="voice"
            )
            input_voice = EvidenceInput(
                investigation_id=investigation.id,
                modality=Modality.VOICE.value,
                file_path=file_path
            )
            db.add(input_voice)

        # Commit all changes atomically
        db.commit()
        db.refresh(investigation)
        return investigation

    except Exception as e:
        db.rollback()
        logger.error(f"Failed to ingest investigation: {e!s}")
        raise


# Backwards compatibility alias for investigation creation
create_investigation = ingest_investigation

