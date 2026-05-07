# LLD Refactor & Cleanup — Progress Tracker

> This file tracks our step-by-step refactor of the Tender Intelligence System.
> Updated as we go. Each module includes the concept, the mini-task, and the status.

---

## Part 1 — Codebase Cleanup

| Task | Status | Notes |
|---|---|---|
| Delete typo `_init__.py` files (processors, scheduler, utils) | DONE | Replaced by correct `__init__.py` |
| Delete `testmodule.py` | DONE | Dev scratch script |
| Delete `ask_chatbot.py` | DONE | Redundant one-liner wrapper |
| Delete `scraper/captch_cnn_solver.py` | DONE | 125 lines, entirely commented out |
| Delete `debug_processed_captcha.png` | DONE | Debug artifact |
| Delete `scraper/web_selectors.py` | DONE | Empty, never imported |
| Delete `processors/` folder | DONE | Duplicate + contradictory logic — see Module 4 |
| Move `connection_check/` → `scripts/` | DONE | Diagnostic scripts not part of the module |
| Move `storage/vector_store.py` → `scripts/test_search.py` | DONE | Manual test script |
| Move `create_qdrant_collection.py` → `scripts/setup_qdrant.py` | DONE | One-off setup script |
| Delete `services/test_chat_service.py` | DONE | Ollama ping test |
| Delete `scraper/base.py.bk`, `scraper/base_new.py.bk` | DONE | Manual git-style backups |
| Clean `main.py` — wrap in function, guard, remove dead code | DONE | Now has `run_pipeline()` + `if __name__ == "__main__"` |
| Clean `chatbot.py` — strip 180 lines of commented experiments | DONE | |
| Clean `postgres.py` — fix import bug, strip dead code | DONE | `from config import settings` → `from ingestion_engine.config import settings` |
| Add `pydantic-settings` to `pyproject.toml` | DONE | Was missing; caused ImportError on fresh install |
| Add `try/except` to `document_ingestion_workflow.py` | DONE | One bad PDF no longer kills the whole pipeline |
| Rename `base_clean.py` → `scraper_runner.py` | DONE | Was the real entry point — misleading name fixed |
| Rename `eprocure_scraper.py` → `download_handler.py` | DONE | Only handles downloads, not a full scraper |
| Update `README.md` | DONE | Reflects current clean structure |

---

## Part 2 — LLD Teaching Modules

### Module 1 — Single Responsibility Principle (SRP)
> **One class = one reason to change**

- **Files created:** `tender_parser.py`, `tender_builder.py`, `tender_repository.py`
- **Deleted:** `tenderservice.py`
- **Concept learned:** One class = one reason to change. Anything that takes a `session` belongs in the repository, not the builder.
- **Interview question:** "Tell me about a time you refactored a God class"
- **Status:** DONE

---

### Module 2 — Dependency Inversion Principle (DIP)
> **Depend on abstractions, not concrete implementations**

- **Files refactored:** `vector_index_service.py`, `vector_search_service.py`, `chatbot.py`, `document_ingestion_workflow.py`, `main.py`
- **Concept learned:** Classes should receive dependencies, not create them. Anything that opens a connection or loads a model must be injected.
- **Bonus learned:** Creating services inside a loop (per tender) reloads the 120MB model every iteration — injecting once and reusing saves massive cost.
- **Interview question:** "How do you make code testable?"
- **Status:** DONE

---

### Module 3 — Open/Closed Principle (OCP)
> **Open for extension, closed for modification**

- **File refactored:** `services/chunking_service.py`
- **Concept learned:** Strategy Pattern — define a contract (ABC), implement it, inject it. New strategies = new classes, zero changes to existing code.
- **Bonus learned:** `@staticmethod`-only class is a function in disguise — Strategy pattern solves both the OCP violation and the design smell.
- **Interview question:** "How do you design for extensibility without breaking existing code?"
- **Status:** DONE

---

### Module 4 — DRY Principle + Architecture (Processors vs Services)
> **Don't repeat yourself. Know where logic belongs.**

- **File:** `processors/chunker.py` (now deleted)
- **Lesson learned:** `processors/` had identical code to `services/` + contradictory OpenAI embedder
- **Rule going forward:** Processors = pure data transformation (no DB, no config, no network). Services = orchestrators.
- **Interview question:** "How do you structure a data pipeline for testability?"
- **Status:** CONCEPT TAUGHT — cleanup done

---

### Module 5 — Logging + Observability
> **`print()` is not logging. Production needs levels, timestamps, and structure.**

- **Files done:** All files — zero `print()` calls remain in the entire module
- **Bonus fix:** `captcha_solver.py` had a broken import (`captch_cnn_solver`) from the deleted CNN file — caught and removed
- **Bonus fix:** `chat_service.py` hardcoded `http://localhost:11434` — moved to `settings.ollama_base_url`
- **Concept learned:** Log levels (DEBUG/INFO/WARNING/ERROR) let you filter noise. `print()` treats a progress update and a crash identically.
- **Log format:** `2026-05-02 22:43:58 | WARNING  | module.name | message`
- **Interview question:** "How do you debug a production pipeline failure at 3am?"
- **Status:** DONE

---

## Phase 2 — FastAPI Layer

| Endpoint | File | Status |
|---|---|---|
| `GET /health` | `api/routes/health.py` | DONE |
| `POST /query` | `api/routes/query.py` | DONE |
| `POST /ingest` | `api/routes/ingest.py` | DONE |
| `GET /tenders` | `api/routes/tenders.py` | DONE |

- **Schemas:** `api/schemas.py` — Pydantic request/response models (separate from DB models)
- **Dependencies:** `api/dependencies.py` — FastAPI `Depends()` providers for DB session and services
- **App factory:** `api/app.py` — lifespan startup loads QdrantClient + EmbeddingService once
- **Run:** `uvicorn ingestion_engine.api.app:app --reload`
- **Docs:** http://localhost:8000/docs (auto-generated Swagger UI)
- **Note:** `POST /ingest` runs post-scrape pipeline only (metadata → PDF → Qdrant). Playwright scraping still runs as a separate script due to manual CAPTCHA requirement.

---

## Phase 3 — Docker + Cloud Deployment

- [ ] Add `ingestion_engine` as a proper Docker service in `docker-compose.yml`
- [ ] Switch LLM from Ollama (local) to Claude API (cloud-compatible)
- [ ] Deploy to cloud (Railway / Render / AWS)

---

## Key Concepts Covered So Far

| Concept | Where we saw it |
|---|---|
| Module-level execution (bad) | `main.py` running code at import time |
| `if __name__ == "__main__"` guard | Fixed in `main.py` |
| Wrong import path | `from config import settings` in `postgres.py` |
| Dead code cost | 180 commented lines in `chatbot.py` |
| Processors vs Services | `processors/` folder decision |
| DRY violation | `processors/chunker.py` duplicating `services/chunking_service.py` |
| Defensive error handling | `try/except` in `document_ingestion_workflow.py` |
