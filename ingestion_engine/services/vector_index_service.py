import hashlib
import uuid

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, FieldCondition, Filter, MatchValue, PointStruct, VectorParams

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

    def _already_indexed(self, document: str, chunk_index: int) -> bool:
        chunk_id = hashlib.md5(f"{document}:{chunk_index}".encode()).hexdigest()
        results = self.client.scroll(
            collection_name=self.collection,
            scroll_filter=Filter(
                must=[FieldCondition(key="chunk_id", match=MatchValue(value=chunk_id))]
            ),
            limit=1,
        )
        return len(results[0]) > 0

    def upsert(self, vectors: list, metadatas: list[dict]) -> None:
        points = []
        for vector, meta in zip(vectors, metadatas):
            document = meta.get("document", "")
            chunk_index = meta.get("chunk_index", 0)
            chunk_id = hashlib.md5(f"{document}:{chunk_index}".encode()).hexdigest()

            if self._already_indexed(document, chunk_index):
                continue

            points.append(
                PointStruct(
                    id=str(uuid.uuid4()),
                    vector=vector,
                    payload={**meta, "chunk_id": chunk_id},
                )
            )

        if points:
            self.client.upsert(collection_name=self.collection, points=points)
