from __future__ import annotations

import logging

from app.core.config import settings
from app.core.errors import ValidationError

logger = logging.getLogger("threatweave-api.validation")


def validate_image_file(file_bytes: bytes, filename: str) -> None:
    """
    Validates that an image file meets size and type constraints.
    Instead of trusting Content-Type, checks magic bytes/signatures for JPEG, PNG, and WebP.
    """
    max_bytes = settings.MAX_IMAGE_SIZE_MB * 1024 * 1024
    actual_size = len(file_bytes)

    if actual_size > max_bytes:
        logger.warning(f"File {filename} rejected: size {actual_size} exceeds {max_bytes} bytes")
        raise ValidationError(
            message=f"Image file exceeds maximum limit of {settings.MAX_IMAGE_SIZE_MB}MB",
            code="file_too_large"
        )

    # Validate Magic Bytes / Signatures
    # JPEG signature: \xff\xd8\xff
    is_jpeg = file_bytes.startswith(b"\xff\xd8\xff")

    # PNG signature: \x89PNG\r\n\x1a\n
    is_png = file_bytes.startswith(b"\x89PNG\r\n\x1a\n")

    # WebP signature: RIFFxxxxWEBP (RIFF at index 0, WEBP at index 8)
    is_webp = (
        len(file_bytes) >= 12
        and file_bytes.startswith(b"RIFF")
        and file_bytes[8:12] == b"WEBP"
    )

    if not (is_jpeg or is_png or is_webp):
        logger.warning(f"File {filename} rejected: invalid image signature")
        raise ValidationError(
            message="Invalid image file format. Only JPEG, PNG, and WebP are allowed.",
            code="invalid_file_format"
        )


def validate_audio_file(file_bytes: bytes, filename: str) -> None:
    """
    Validates that an audio file meets size and type constraints.
    Checks magic bytes/signatures for WAV, MP3, and M4A.
    """
    max_bytes = settings.MAX_AUDIO_SIZE_MB * 1024 * 1024
    actual_size = len(file_bytes)

    if actual_size > max_bytes:
        logger.warning(f"File {filename} rejected: size {actual_size} exceeds {max_bytes} bytes")
        raise ValidationError(
            message=f"Audio file exceeds maximum limit of {settings.MAX_AUDIO_SIZE_MB}MB",
            code="file_too_large"
        )

    # Validate Magic Bytes / Signatures
    # WAV signature: RIFFxxxxWAVE (RIFF at index 0, WAVE at index 8)
    is_wav = (
        len(file_bytes) >= 12
        and file_bytes.startswith(b"RIFF")
        and file_bytes[8:12] == b"WAVE"
    )

    # MP3 signature: ID3 header or MPEG sync frame starting with 0xFF and three high bits set (\xff\xfx or \xff\xe0)
    is_mp3 = file_bytes.startswith(b"ID3") or (
        len(file_bytes) >= 2
        and file_bytes[0] == 0xFF
        and (file_bytes[1] & 0xE0) == 0xE0
    )

    # M4A signature: ftyp box at offset 4 with brand containing M4A , mp42, isom, dash
    is_m4a = False
    if len(file_bytes) >= 12 and b"ftyp" in file_bytes[4:8]:
        brand = file_bytes[8:12]
        if brand in (b"M4A ", b"mp42", b"isom", b"dash"):
            is_m4a = True

    if not (is_wav or is_mp3 or is_m4a):
        logger.warning(f"File {filename} rejected: invalid audio signature")
        raise ValidationError(
            message="Invalid audio file format. Only WAV, MP3, and M4A are allowed.",
            code="invalid_file_format"
        )


def validate_text_length(text: str) -> None:
    """
    Validates that raw text input does not exceed character limits.
    """
    if len(text) > settings.MAX_TEXT_CHARS:
        logger.warning(f"Text input rejected: length {len(text)} exceeds {settings.MAX_TEXT_CHARS} chars")
        raise ValidationError(
            message=f"Text input exceeds maximum limit of {settings.MAX_TEXT_CHARS} characters",
            code="text_too_long"
        )
