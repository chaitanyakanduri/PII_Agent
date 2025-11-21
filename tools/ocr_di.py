import os
import time
import httpx
from typing import Tuple
from tools.logger import get_logger

logger = get_logger(__name__)

DI_VERSION = "2023-07-31"
READ_URL_SUFFIX = f"/formrecognizer/documentModels/prebuilt-read:analyze?api-version={DI_VERSION}"

class AzureDIError(RuntimeError):
    pass

def _headers():
    key = os.getenv("AZURE_DI_KEY")
    if not key:
        raise AzureDIError("AZURE_DI_KEY not set")
    return {"Ocp-Apim-Subscription-Key": key}

def _endpoint():
    ep = os.getenv("AZURE_DI_ENDPOINT")
    if not ep:
        raise AzureDIError("AZURE_DI_ENDPOINT not set")
    return ep.rstrip("/")

def ocr_file_to_text(file_bytes: bytes, content_type: str) -> Tuple[str, dict]:
    endpoint = _endpoint()
    url = endpoint + READ_URL_SUFFIX

    logger.info("Submitting file to Azure DI Read OCR")
    with httpx.Client(timeout=60.0) as client:
        r = client.post(url, headers={**_headers(), "Content-Type": content_type}, content=file_bytes)
        if r.status_code not in (202, 200):
            logger.error("DI analyze start failed: %s - %s", r.status_code, r.text)
            raise AzureDIError(f"Analyze start failed: {r.status_code} {r.text}")

        op = r.headers.get("operation-location") or r.headers.get("Operation-Location")
        if not op:
            data = r.json()
            if "result" in data:
                return _flatten_read_result(data["result"]), data
            raise AzureDIError("Operation-Location missing in response")

        for _ in range(60):
            poll = client.get(op, headers=_headers())
            if poll.status_code != 200:
                time.sleep(1.0)
                continue
            body = poll.json()
            status = (body.get("status") or body.get("statusResult") or "").lower()
            if status in ("succeeded", "success", "ok"):
                full_text = _flatten_read_result(body.get("analyzeResult") or body.get("result") or {})
                return full_text, body
            elif status in ("failed", "error"):
                logger.error("DI analyze failed: %s", body)
                raise AzureDIError(f"Analyze failed: {body}")
            time.sleep(1.0)

        raise AzureDIError("Analyze polling timed out")

def _flatten_read_result(result: dict) -> str:
    pages = result.get("pages") or []
    lines = []
    for p in pages:
        for ln in p.get("lines", []):
            txt = ln.get("content")
            if txt:
                lines.append(txt)
    return "\\n".join(lines).strip()
