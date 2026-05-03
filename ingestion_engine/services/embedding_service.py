import torch
from sentence_transformers import SentenceTransformer

from ingestion_engine.config import settings


class EmbeddingService:

    def __init__(self):
        device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = SentenceTransformer(settings.embedding_model, device=device)
        self._query_cache: dict[str, list[float]] = {}

    def embed_documents(self, docs: list[str]) -> list[list[float]]:
        prefixed = [f"Represent this document for retrieval: {d}" for d in docs]
        embeddings = self.model.encode(
            prefixed,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return embeddings.tolist()

    def embed_query(self, query: str) -> list[float]:
        if not query:
            return []
        if query in self._query_cache:
            return self._query_cache[query]
        prefixed = f"Represent this query for retrieval: {query}"
        embedding = self.model.encode(
            prefixed,
            normalize_embeddings=True,
            show_progress_bar=False,
        ).tolist()
        self._query_cache[query] = embedding
        if len(self._query_cache) > 256:
            self._query_cache.pop(next(iter(self._query_cache)))
        return embedding
