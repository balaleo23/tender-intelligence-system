import requests
from fastapi import APIRouter
from sqlalchemy import text

from ingestion_engine.api.schemas import HealthResponse
from ingestion_engine.config import settings
from ingestion_engine.storage.postgres import get_session

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    results: dict[str, str] = {"postgres": "down", "qdrant": "down", "ollama": "down"}

    try:
        with get_session() as session:
            session.execute(text("SELECT 1"))
        results["postgres"] = "up"
    except Exception:
        pass

    try:
        from qdrant_client import QdrantClient
        QdrantClient(host=settings.qdrant_host, port=settings.qdrant_port).get_collections()
        results["qdrant"] = "up"
    except Exception:
        pass

    try:
        r = requests.get(f"{settings.ollama_base_url}/api/tags", timeout=3.0)
        if r.status_code == 200:
            results["ollama"] = "up"
    except Exception:
        pass

    status = "ok" if all(v == "up" for v in results.values()) else "degraded"
    return HealthResponse(status=status, **results)
