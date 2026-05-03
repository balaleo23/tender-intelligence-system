"""
Scrape route — triggers the Playwright scraper as a background thread.

Key design decisions:
1. Returns immediately (non-blocking) — scraper runs in a ThreadPoolExecutor
2. Guards against concurrent runs — 409 if already running
3. Tracks status in memory — GET /scrape/status for polling
"""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, HTTPException

from ingestion_engine.api.schemas import ScrapeStatusResponse
from ingestion_engine.scraper.scraper_runner import Scrapper
from ingestion_engine.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/scrape", tags=["scrape"])

# ── In-memory status tracker ──────────────────────────────────────────────────
# Simple dict — no Redis needed for portfolio.
# Lives as long as the server process runs.
# Reset to idle on server restart (acceptable for our use case).
_status: dict = {
    "state": "idle",          # idle | running | done | failed
    "tenders_scraped": 0,
    "error": None,
    "started_at": None,
    "finished_at": None,
}

# max_workers=1 — only one scraper runs at a time (same site, same files)
_executor = ThreadPoolExecutor(max_workers=1)


# ── The actual scraper logic (runs in a thread) ───────────────────────────────

def _run_scraper() -> None:
    """
    Runs synchronously inside a ThreadPoolExecutor thread.
    FastAPI's event loop is completely free while this executes.
    Updates _status so the polling endpoint can report progress.
    """
    global _status

    _status["state"] = "running"
    _status["started_at"] = datetime.now(timezone.utc).isoformat()
    _status["tenders_scraped"] = 0
    _status["error"] = None
    _status["finished_at"] = None

    scrapper = Scrapper()
    try:
        logger.info("Scraper thread started")
        page = scrapper.open_load_content()
        scrapper.extract_rows(page)
        scrapper.form_json()

        tenders_scraped = len(scrapper.data)
        _status["state"] = "done"
        _status["tenders_scraped"] = tenders_scraped
        _status["finished_at"] = datetime.now(timezone.utc).isoformat()
        logger.info("Scraper finished — %d tenders scraped", tenders_scraped)

    except Exception as e:
        _status["state"] = "failed"
        _status["error"] = str(e)
        _status["finished_at"] = datetime.now(timezone.utc).isoformat()
        logger.error("Scraper failed: %s", e)

    finally:
        scrapper.close()


# ── Routes ────────────────────────────────────────────────────────────────────

@router.post("", response_model=ScrapeStatusResponse)
async def trigger_scrape() -> ScrapeStatusResponse:
    """
    POST /scrape
    Starts the scraper in a background thread.
    Returns immediately — use GET /scrape/status to track progress.

    NOTE: Scraper requires a visible browser for captcha solving.
    Run scripts/run_scraper.py locally instead of using this endpoint
    when captcha solving is needed.

    409 if a scrape is already running.
    """
    # Guard — prevent concurrent scrapes
    if _status["state"] == "running":
        raise HTTPException(
            status_code=409,
            detail="A scrape is already in progress. Check /scrape/status for updates."
        )

    # Push blocking scraper to thread — event loop stays free
    loop = asyncio.get_event_loop()
    loop.run_in_executor(_executor, _run_scraper)

    logger.info("Scrape triggered — running in background thread")
    return ScrapeStatusResponse(
        state="running",
        tenders_scraped=0,
        error=None,
        started_at=None,
        finished_at=None,
        message="Scraping started. Poll /scrape/status for progress.",
    )


@router.get("/status", response_model=ScrapeStatusResponse)
def scrape_status() -> ScrapeStatusResponse:
    """
    GET /scrape/status
    Returns current scraper state.
    Streamlit polls this every few seconds to show live progress.
    """
    return ScrapeStatusResponse(
        state=_status["state"],
        tenders_scraped=_status["tenders_scraped"],
        error=_status["error"],
        started_at=_status["started_at"],
        finished_at=_status["finished_at"],
        message=_message_for_state(_status["state"]),
    )


def _message_for_state(state: str) -> str:
    return {
        "idle": "No scrape has been run yet.",
        "running": "Scraping in progress...",
        "done": "Scraping completed successfully.",
        "failed": "Scraping failed. Check the error field.",
    }.get(state, "Unknown state.")
