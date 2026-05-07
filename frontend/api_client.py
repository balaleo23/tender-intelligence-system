"""
API client for the Tender Intelligence backend.

Every function maps 1-to-1 with a FastAPI endpoint.
UI code (Streamlit today, React tomorrow) never calls requests directly.
This file is the single source of truth for what the backend can do.
"""

import os

import requests

# Read from environment — works both locally and in Docker
# Locally:  API_BASE_URL=http://localhost:8000
# Docker:   API_BASE_URL=http://api:8000  (set in docker-compose.yml)
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

# How long to wait for API responses (seconds)
# /query can take 10-15s (embedding + LLM), /ingest and /scrape can take minutes
DEFAULT_TIMEOUT = 300  # 5 minutes — /query runs embedding + LLM which can be slow
INGEST_TIMEOUT = 1800  # 30 minutes — PDF extraction + embedding + Qdrant upserts
SCRAPE_TIMEOUT = 300  # 5 minutes — scraper is slow


# ── Exceptions ────────────────────────────────────────────────────────────────

class APIError(Exception):
    """Raised when the backend returns an error response."""
    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"API error {status_code}: {detail}")


# ── Helper ────────────────────────────────────────────────────────────────────

def _post(endpoint: str, payload: dict, timeout: int = DEFAULT_TIMEOUT) -> dict:
    """
    Central HTTP helper — all POST calls go through here.
    Raises APIError on non-2xx responses so UI can handle cleanly.
    """
    url = f"{API_BASE_URL}{endpoint}"
    try:
        response = requests.post(url, json=payload, timeout=timeout)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        raise APIError(503, "Cannot reach the API. Is the backend running?")
    except requests.exceptions.Timeout:
        raise APIError(504, f"Request timed out after {timeout}s.")
    except requests.exceptions.HTTPError as e:
        detail = e.response.json().get("detail", str(e)) if e.response else str(e)
        raise APIError(e.response.status_code, detail)


def _get(endpoint: str, timeout: int = DEFAULT_TIMEOUT) -> dict:
    """Central HTTP helper for GET calls."""
    url = f"{API_BASE_URL}{endpoint}"
    try:
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        raise APIError(503, "Cannot reach the API. Is the backend running?")
    except requests.exceptions.Timeout:
        raise APIError(504, f"Request timed out after {timeout}s.")
    except requests.exceptions.HTTPError as e:
        detail = e.response.json().get("detail", str(e)) if e.response else str(e)
        raise APIError(e.response.status_code, detail)


# ── Public API functions ───────────────────────────────────────────────────────
# These are what UI code calls. Each one = one backend endpoint.
# When moving to React, a developer reads these to understand the API contract.

def health_check() -> dict:
    """
    GET /health
    Returns: { status, postgres, qdrant, ollama }
    """
    return _get("/health")


def search_tenders(question: str) -> dict:
    """
    POST /query
    Returns: { answer: str, citations: list[str], confidence: float }
    """
    return _post("/query", {"question": question})


def trigger_ingestion() -> dict:
    """
    POST /ingest
    Reads from meta_data/ folder on the server.
    Returns: { message: str, tenders_processed: int }
    """
    return _post("/ingest", {}, timeout=INGEST_TIMEOUT)


def trigger_scrape() -> dict:
    """
    POST /scrape
    Starts the scraper in a background thread. Returns immediately.
    Returns: { state, message, tenders_scraped, ... }
    409 if already running.
    """
    return _post("/scrape", {}, timeout=DEFAULT_TIMEOUT)


def get_scrape_status() -> dict:
    """
    GET /scrape/status
    Poll this to track scraper progress.
    Returns: { state, tenders_scraped, error, started_at, finished_at, message }
    """
    return _get("/scrape/status")


def list_tenders() -> list[dict]:
    """
    GET /tenders
    Returns: list of { tender_uid, title, organization, published_date, bid_submission_end_date }
    """
    return _get("/tenders")
