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

    def _indexed_chunk_ids(self, document: str) -> set[str]:
        """Fetch all chunk_ids already stored for a document in one scroll."""
        known = set()
        offset = None
        while True:
            batch, offset = self.client.scroll(
                collection_name=self.collection,
                scroll_filter=Filter(
                    must=[FieldCondition(key="document", match=MatchValue(value=document))]
                ),
                with_payload=["chunk_id"],
                limit=100,
                offset=offset,
            )
            for point in batch:
                cid = point.payload.get("chunk_id")
                if cid:
                    known.add(cid)
            if offset is None:
                break
        return known

    def upsert(self, vectors: list, metadatas: list[dict]) -> None:
        if not vectors:
            return

        # Batch-fetch all already-indexed chunk_ids for this document (1 Qdrant call)
        document = metadatas[0].get("document", "") if metadatas else ""
        known_ids = self._indexed_chunk_ids(document) if document else set()

        points = []
        for vector, meta in zip(vectors, metadatas):
            chunk_id = hashlib.md5(
                f"{meta.get('document', '')}:{meta.get('chunk_index', 0)}".encode()
            ).hexdigest()
            if chunk_id in known_ids:
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
