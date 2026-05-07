# Copilot Instructions for Tender Intelligence System

## Overview
This is an end-to-end tender ingestion and Agentic RAG system for Indian government portals, specifically targeting eprocure.gov.in. The system automates scraping tender documents, processing PDFs, generating embeddings, and storing data for retrieval-augmented generation.

## Architecture
The system follows a modular pipeline architecture with clear separation of concerns:

- **Ingestion Engine**: Core pipeline handling scraping, processing, storage, and scheduling
- **Agentic RAG**: Future phase for intelligent query processing (keep separate)
- **Scripts**: Utility scripts for database setup and one-off runs
- **Tests**: Component-specific test suites

## Key Components

### Scraper (`ingestion_engine/scraper/`)
- Browser automation for eprocure.gov.in using Selenium/Playwright
- Abstract base scraper in `base.py` for extensibility
- Captcha solving via 2Captcha/OCR in `captcha_solver.py`
- Isolated CSS/XPath selectors in `selectors.py` to avoid tight coupling

### Processors (`ingestion_engine/processors/`)
- `pdf_downloader.py`: Fetch and store PDF documents
- `pdf_parser.py`: Text extraction using PyPDF2/unstructured
- `chunker.py`: Token-based text chunking for embeddings
- `embedder.py`: OpenAI embeddings generation

### Storage (`ingestion_engine/storage/`)
- `postgres.py`: Tender metadata storage
- `vector_store.py`: Vector database interface for embeddings
- `models.py`: SQLAlchemy ORM models

### Scheduler (`ingestion_engine/scheduler/`)
- `cron.py`: APScheduler/Celery beat for periodic ingestion
- `tasks.py`: Individual ingestion job definitions

### Utils (`ingestion_engine/utils/`)
- `logger.py`: Centralized logging configuration
- `rate_limiter.py`: Exponential backoff for API calls
- `retry.py`: Retry policies for resilient operations

### Config (`ingestion_engine/config/`)
- `settings.py`: Environment-based configuration
- `constants.py`: Project constants

## Data Flow
1. Scheduler triggers ingestion tasks
2. Scraper browses eprocure.gov.in, solves captchas, extracts tender links
3. PDF downloader fetches documents
4. PDF parser extracts text content
5. Chunker splits text into token-based chunks
6. Embedder generates OpenAI embeddings
7. Data stored in Postgres (metadata) and vector store (embeddings)

## Development Workflow
- Use Docker Compose for local development: `docker-compose up`
- Run scraper manually: `python scripts/run_scraper_once.py`
- Bootstrap database: `python scripts/bootstrap_db.py`
- Entry point: `python ingestion_engine/main.py`

## Conventions
- Isolate selectors in `selectors.py` to prevent scraper brittleness
- Use exponential backoff in `rate_limiter.py` for all external API calls
- Centralize logging via `utils/logger.py`
- Follow SQLAlchemy patterns in `storage/models.py`
- Keep agentic RAG logic separate from ingestion pipeline

## Dependencies
- PyPDF2/unstructured for PDF processing
- OpenAI API for embeddings
- SQLAlchemy for ORM
- APScheduler/Celery for scheduling
- Selenium/Playwright for browser automation
- 2Captcha/OCR for captcha solving

## Testing
- Test suites in `tests/` mirror component structure
- Focus on scraper reliability, processor accuracy, storage integrity

## Deployment
- Containerized with Docker Compose
- Environment variables via `.env` file
- CI/CD via `.github/workflows/ci.yml`