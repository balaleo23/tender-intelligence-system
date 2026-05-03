import torch
from sentence_transformers import SentenceTransformer

from ingestion_engine.config import settings

class EmbeddingService:

        def __init__(self):
            device = "cuda" if torch.cuda.is_available() else "cpu"
            self.model = SentenceTransformer(settings.embedding_model, device= device)
            # self.model = SentenceTransformer("BAAI/bge-small-en-v1.5" , device=device)

        def embed_documents(self, docs: list[str]) -> list[list[float]]:
            docs = [f"Represent this document for retrieval: {d}" for d in docs]
            embeddings = self.model.encode(
                docs,
                normalize_embeddings=True,
                show_progress_bar=False
            )
            return embeddings.tolist()

        def embed_query(self, query: str) -> list[float]:
            if not query:
                return []
            query = f"Represent this query for retrieval: {query}"
            embedding = self.model.encode(
                query,
                normalize_embeddings=True,
                show_progress_bar=False
            )
            return embedding.tolist()

