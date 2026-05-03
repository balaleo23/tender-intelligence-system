from qdrant_client import QdrantClient

from ingestion_engine.config import settings
from ingestion_engine.services.embedding_service import EmbeddingService


class VectorSearchService:

    def __init__(self, client: QdrantClient, embedder: EmbeddingService):
        self.qdrant = client
        self.embedder = embedder
        self.collection = settings.collection_name

    def search(self, query: str, top_k: int = None, score_threshold: float = None) -> list:
        top_k = top_k or settings.top_k
        score_threshold = score_threshold if score_threshold is not None else settings.score_threshold
        query_vector = self.embedder.embed_query(query)
        results = self.qdrant.query_points(
            collection_name=self.collection,
            query=query_vector,
            limit=top_k,
            score_threshold=score_threshold,
        )
        return results.points
