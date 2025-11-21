import os
from typing import Dict, Any
from tools.pdf_utils import any_to_text
from tools.pii_detect import load_policy, detect, redact
from tools.logger import get_logger

logger = get_logger(__name__)

def maybe_context_hints(text: str) -> dict:
    if not (os.getenv("AZURE_OPENAI_ENDPOINT") and os.getenv("AZURE_OPENAI_API_KEY") and os.getenv("AZURE_OPENAI_DEPLOYMENT")):
        return {"enabled": False, "notes": "Azure OpenAI not configured"}
    return {"enabled": True, "notes": "Azure OpenAI configured; policy-based redaction still authoritative"}

def process_bytes(file_bytes: bytes, content_type: str) -> Dict[str, Any]:
    logger.info("Starting redaction pipeline (Presidio) for content-type=%s", content_type)
    text, ocr_meta = any_to_text(file_bytes, content_type)
    logger.debug("Extracted text length: %d", len(text))

    policies = load_policy()
    entities = detect(text, policies)
    redacted_text = redact(text, policies, entities)

    hints = maybe_context_hints(text)

    result = {
        "content_type": content_type,
        "text_length": len(text),
        "entities": entities,
        "redacted_text": redacted_text,
        "ocr_meta_present": bool(ocr_meta),
        "aoai_hints": hints,
    }
    logger.info("Redaction complete: %d entities found (Presidio)", len(entities))
    return result
