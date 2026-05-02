# Tender Intelligence System

End-to-end tender ingestion and Agentic RAG system for Indian government procurement portals.

Scrapes tender documents from [eprocure.gov.in](https://eprocure.gov.in), processes and embeds them into a vector store, and exposes a RAG-powered chatbot for intelligent querying over procurement data.

---

## Architecture Overview

```
eprocure.gov.in
    ↓  Playwright browser automation
Scraper  →  Download PDFs / ZIPs
    ↓
Metadata extracted  →  PostgreSQL  (Tender, Organization, TenderDocument, IngestionLog)
    ↓
ZIP Extraction  →  data/tenders/<year>/<month>/<tender_uid>/extracted/
    ↓
PDF Text Extraction  (PyPDF2 + OCR fallback via Tesseract / EasyOCR)
    ↓
Chunking Service  (800-word chunks, 100-word overlap)
    ↓
Embedding Service  (BAAI/bge-small-en-v1.5, 384-dim)
    ↓
Qdrant Vector Store  (COSINE distance)
    ↓
Ollama RAG Chatbot  →  Structured response: answer + citations + confidence
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Web Scraping | Playwright (Chromium) |
| PDF Extraction | PyPDF2, pdf2image, pytesseract, EasyOCR |
| Vector Database | Qdrant |
| Embeddings | Sentence-Transformers (`BAAI/bge-small-en-v1.5`) |
| Relational DB | PostgreSQL 15 + SQLAlchemy ORM |
| LLM (local) | Ollama (Mistral / Llama 3) |
| Infrastructure | Docker Compose |
| Python | 3.10+ |

---

## Prerequisites

### System Dependencies

**Windows:**
- [Tesseract OCR](https://github.com/UB-Mannheim/tesseract/wiki) — install and note the path (e.g. `C:\Program Files\Tesseract-OCR\tesseract.exe`)
- [Poppler for Windows](https://github.com/oschwartz10612/poppler-windows/releases) — extract and note the `bin/` path

**Linux / macOS:**
```bash
# Ubuntu/Debian
sudo apt-get install tesseract-ocr poppler-utils

# macOS
brew install tesseract poppler
```

### Python

Python 3.10 or higher is required. Install [uv](https://docs.astral.sh/uv/) (recommended) or use pip.

### Docker

[Docker Desktop](https://www.docker.com/products/docker-desktop/) is required for the infrastructure services.

---

## Setup

### Step 1 — Clone the repository

```bash
git clone <repo-url>
cd tender-intelligence-system
```

### Step 2 — Configure environment variables

```bash
cp .env.example .env
```

Edit `.env`:

```env
POSTGRES_URL=postgresql+psycopg2://tender_user:tender_pass@localhost:5432/tender_db
QDRANT_HOST=localhost
QDRANT_PORT=6333
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=mistral

# Windows only
TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe
POPPLER_PATH=C:\poppler\poppler-25.12.0\Library\bin
```

### Step 3 — Start infrastructure services

```bash
docker-compose up -d
```

| Service | Port | Purpose |
|---|---|---|
| PostgreSQL | 5432 | Tender metadata, documents, audit logs |
| Qdrant | 6333 / 6334 | Vector store for document embeddings |
| Ollama | 11434 | Local LLM inference |

### Step 4 — Pull an LLM model into Ollama

```bash
docker exec tender_ollama ollama pull mistral
```

### Step 5 — Install Python dependencies

```bash
# Using uv (recommended)
uv sync

# Using pip
pip install -e .
```

### Step 6 — Install Playwright browsers

```bash
playwright install chromium
```

---

## Running the Pipeline

### Step 7 — Scrape tenders from eprocure.gov.in

```bash
python -m ingestion_engine.scraper.scraper_runner
```

Downloaded files land in `data/tenders/<year>/<month>/<tender_uid>/raw/`.
Metadata JSONs are written to `meta_data/`.

### Step 8 — Run the ingestion pipeline

```bash
python -m ingestion_engine.main
```

What this does:

1. Reads `meta_data/*Tender_data*.json` and `meta_data/*Tenders_filepath*.json`
2. Creates `Organization` and `Tender` records in PostgreSQL (skips duplicates by `tender_uid`)
3. Registers `TenderDocument` records with MD5 checksums
4. For each tender, runs the document processing pipeline:
   - Extracts ZIP archives
   - Extracts text from PDFs (PyPDF2 + OCR fallback for scanned documents)
   - Splits text into 800-word overlapping chunks
   - Embeds each chunk with Sentence-Transformers
   - Upserts vectors into Qdrant with full metadata payload

---

## Querying the Chatbot

```python
from ingestion_engine.chatbot import ask_chatbot_structured

response = ask_chatbot_structured("What road construction tenders are available in Tamil Nadu?")

print(response["answer"])
print("Sources:", response["citations"])
print("Confidence:", response["confidence"])
```

Response shape:

```json
{
  "answer": "There are 3 road construction tenders...",
  "citations": ["2024_PWD_001_01", "2024_PWD_003_01"],
  "confidence": 0.87
}
```

---

## Directory Structure

```
tender-intelligence-system/
├── docker-compose.yml
├── pyproject.toml
├── .env.example
├── scripts/                             # Ops and diagnostic scripts (not part of module)
│   ├── check_postgres.py
│   ├── check_qdrant.py
│   ├── check_ollama.py
│   ├── setup_qdrant.py
│   └── test_search.py
└── ingestion_engine/
    ├── main.py                          # Pipeline entry point — run_pipeline()
    ├── chatbot.py                       # RAG chatbot — ask_chatbot_structured()
    ├── document_ingestion_workflow.py   # Orchestrates extraction → embedding → upsert
    ├── config.py                        # Pydantic settings loader (.env)
    ├── scraper/
    │   ├── scraper_runner.py            # Entry point — Scrapper class, page navigation, JSON output
    │   ├── download_handler.py          # File download logic (called by scraper_runner)
    │   └── captcha_solver.py            # CAPTCHA handling
    ├── services/
    │   ├── document_service.py          # PDF text extraction + OCR fallback
    │   ├── extraction_service.py        # ZIP extraction
    │   ├── chunking_service.py          # Text chunking (800 words, 100 overlap)
    │   ├── embedding_service.py         # Sentence-Transformers embeddings
    │   ├── vector_index_service.py      # Qdrant upsert
    │   ├── vector_search_service.py     # Qdrant semantic search
    │   ├── chat_service.py              # Ollama chat wrapper
    │   ├── tenderservice.py             # Tender creation + deduplication
    │   └── organization_service.py      # Organisation hierarchy management
    ├── storage/
    │   ├── models.py                    # SQLAlchemy ORM models
    │   └── postgres.py                  # Engine + session factory
    └── utils/
        ├── file_manager_dir.py          # Tender directory structure manager
        └── logger.py                    # Centralised logger (in progress)
```

---

## Database Schema

| Table | Description |
|---|---|
| `organizations` | Hierarchical org structure (parent-child) |
| `tenders` | Core tender metadata (uid, title, dates, org, source URL) |
| `tender_documents` | PDF metadata (filename, checksum, storage path, size) |
| `tender_ingestion_logs` | Audit trail for each ingestion run (status, errors) |

Tables are created automatically on first run via `init_db()`.

---

## Troubleshooting

**PostgreSQL connection refused**
Ensure Docker containers are running: `docker-compose ps`.

**Tesseract not found (Windows)**
Set `TESSERACT_CMD` in `.env` to the full path of `tesseract.exe`.

**Poppler not found (Windows)**
Set `POPPLER_PATH` in `.env` to the `bin\` directory of your Poppler installation.

**Ollama model not found**
Run `docker exec tender_ollama ollama pull mistral`.

**Playwright browser not installed**
Run `playwright install chromium`.

**Qdrant collection not found**
Collection is created automatically on first upsert. Ensure Qdrant is running first.

---

## Notes

- Scraper targets tenders closing within the next **14 days** by default.
- Duplicate tenders are skipped based on `tender_uid` — safe to re-run.
- File deduplication uses **MD5 checksums** to avoid re-processing identical documents.
- All LLM inference runs **locally via Ollama** — no external API keys required.
- OCR is used as a fallback for scanned/image-based PDFs.
