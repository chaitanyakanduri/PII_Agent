import io
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from tools.redact import process_bytes
from tools.logger import get_logger
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="PII Redaction AI Agent", version="1.0.0")
logger = get_logger(__name__)

class RedactRequest(BaseModel):
    text: str

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/redact")
async def redact_file(file: UploadFile = File(...)):
    try:
        content = await file.read()
        if not content:
            raise HTTPException(status_code=400, detail="Empty file")
        result = process_bytes(content, file.content_type or "application/octet-stream")
        return JSONResponse(result)
    except Exception as e:
        logger.exception("Redact file failed")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/redact-text")
async def redact_text(payload: RedactRequest):
    try:
        text_bytes = payload.text.encode("utf-8")
        result = process_bytes(text_bytes, "text/plain")
        return JSONResponse(result)
    except Exception as e:
        logger.exception("Redact text failed")
        raise HTTPException(status_code=500, detail=str(e))
