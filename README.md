# PII_Agent — Production-Ready PII Redaction AI Agent (Presidio + Azure DI)

Redacts PII (SSN, Phone, Email, DOB) from text, PDFs, and images.
- OCR via **Azure Document Intelligence (Read)**
- Detection/anonymization via **Microsoft Presidio**
- Optional **Azure OpenAI** for contextual hints (not used for masking)
- REST API (FastAPI) + CLI
- Structured logging (console + rotating file logs in `logs/`)

## Quick Start

### 1) Install
```bash
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m spacy download en_core_web_lg
```
> You can set a lighter spaCy model via `SPACY_MODEL=en_core_web_md` in `.env`.

### 2) Configure
Copy `.env.example` to `.env` and fill in Azure credentials.
```bash
cp .env.example .env
```

Required for OCR:
- `AZURE_DI_ENDPOINT`
- `AZURE_DI_KEY`

Optional for Azure OpenAI (contextual detection helpers):
- `AZURE_OPENAI_ENDPOINT`
- `AZURE_OPENAI_API_KEY`
- `AZURE_OPENAI_DEPLOYMENT`

### 3) Run API
```bash
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

### 4) Try It
```bash
curl -F "file=@/path/to/sample.pdf" http://localhost:8000/redact
```

### 5) CLI
```bash
python runners/cli.py --input /path/to/file.pdf --out /tmp/redacted.txt --entities-json /tmp/entities.json
```

## Policy
Driven by `policies/redaction_policy.yaml` using Presidio entity types:
- `US_SSN`, `EMAIL_ADDRESS`, `PHONE_NUMBER`, `DATE_TIME` (for DOB with context filter).

## Logging
- Console + rotating file logs under `logs/app.log` (keeps 7 days).

## Testing
```bash
pytest -q
```
