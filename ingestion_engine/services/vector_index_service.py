import uuid

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from ingestion_engine.config import settings


class VectorIndexService:

    def __init__(self, client: QdrantClient):
        self.client = client
        self.collection = settings.collection_name
        self._ensure_collection()

    def _ensure_collection(self):
        existing = [c.name for c in self.client.get_collections().collections]
        if self.collection not in existing:
            self.client.create_collection(
                collection_name=self.collection,
                vectors_config=VectorParams(
                    size=settings.embedding_dim,
                    distance=Distance.COSINE,
                ),
            )

    def upsert(self, vectors: list, metadatas: list[dict]) -> None:
        points = [
            PointStruct(id=str(uuid.uuid4()), vector=vector, payload=meta)
            for vector, meta in zip(vectors, metadatas)
        ]
        self.client.upsert(collection_name=self.collection, points=points)
