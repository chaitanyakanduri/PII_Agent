from typing import Dict, Any
from tools.redact import process_bytes
from tools.logger import get_logger

logger = get_logger(__name__)

class PIIRedactionAgent:
    def __init__(self):
        logger.info("PIIRedactionAgent initialized")

    def run(self, file_bytes: bytes, content_type: str) -> Dict[str, Any]:
        logger.debug("Agent run invoked")
        try:
            return process_bytes(file_bytes, content_type)
        except Exception as e:
            logger.error(f"Error during processing: {e}")
            raise
