from typing import Tuple
from tools.ocr_di import ocr_file_to_text
from tools.logger import get_logger

logger = get_logger(__name__)

SUPPORTED_IMAGE_TYPES = {
    "image/png",
    "image/jpeg",
    "image/jpg",
    "image/webp",
    "image/tiff",
}

def any_to_text(file_bytes: bytes, content_type: str) -> Tuple[str, dict]:
    if content_type.startswith("text/") or content_type in {"application/json"}:
        try:
            return file_bytes.decode("utf-8", errors="ignore"), {}
        except Exception:
            return file_bytes.decode("latin-1", errors="ignore"), {}

    if content_type == "application/pdf" or content_type in SUPPORTED_IMAGE_TYPES:
        text, ocr_json = ocr_file_to_text(file_bytes, content_type)
        return text, ocr_json

    logger.warning("Unknown content type '%s', attempting OCR via DI", content_type)
    text, ocr_json = ocr_file_to_text(file_bytes, content_type)
    return text, ocr_json
