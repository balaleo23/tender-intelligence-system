from typing import Generator

from fastapi import Depends, Request
from qdrant_client import QdrantClient
from sqlalchemy.orm import Session

from ingestion_engine.services.chunking_service import ChunkingService
from ingestion_engine.services.embedding_service import EmbeddingService
from ingestion_engine.services.vector_index_service import VectorIndexService
from ingestion_engine.services.vector_search_service import VectorSearchService
from ingestion_engine.storage.postgres import get_session


def get_db() -> Generator[Session, None, None]:
    with get_session() as session:
        yield session


def get_qdrant(request: Request) -> QdrantClient:
    return request.app.state.qdrant


def get_embedder(request: Request) -> EmbeddingService:
    return request.app.state.embedder


def get_searcher(
    client: QdrantClient = Depends(get_qdrant),
    embedder: EmbeddingService = Depends(get_embedder),
) -> VectorSearchService:
    return VectorSearchService(client=client, embedder=embedder)


def get_index(client: QdrantClient = Depends(get_qdrant)) -> VectorIndexService:
    return VectorIndexService(client=client)


def get_chunker() -> ChunkingService:
    return ChunkingService()
