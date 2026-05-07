from contextlib import asynccontextmanager

from fastapi import FastAPI
from qdrant_client import QdrantClient

from ingestion_engine.api.routes import health, ingest, query, scrape, tenders
from ingestion_engine.config import settings
from ingestion_engine.services.embedding_service import EmbeddingService
from ingestion_engine.utils.logger import get_logger
from ingestion_engine.storage.postgres import check_connection , init_db

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up — loading Qdrant client and embedding model")
    app.state.qdrant = QdrantClient(host=settings.qdrant_host, port=settings.qdrant_port)
    app.state.embedder = EmbeddingService()
    check_connection()
    init_db()
    logger.info("Startup complete")
    yield
    logger.info("Shutting down")


def create_app() -> FastAPI:
    app = FastAPI(
        title="Tender Intelligence API",
        description="RAG-powered search and ingestion for Indian government tenders",
        version="0.1.0",
        lifespan=lifespan,
    )
    app.include_router(health.router)
    app.include_router(query.router)
    app.include_router(ingest.router)
    app.include_router(tenders.router)
    app.include_router(scrape.router)
    return app


app = create_app()
