from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct
import uuid
from qdrant_client.models import VectorParams, Distance

class VectorIndexService:

    def __init__(self):
        self.client = QdrantClient(host="localhost", port=6333)
        self.collection = "tenders"
        self._ensure_collection()

    def _ensure_collection(self):
        collections = [c.name for c in self.client.get_collections().collections]

        if self.collection not in collections:
            self.client.create_collection(
                collection_name=self.collection,
                vectors_config=VectorParams(
                    size=384,
                    distance=Distance.COSINE
                )
            )

    def upsert(self, vectors, metadatas):
        points = []

        for vector, meta in zip(vectors, metadatas):
            points.append(
                PointStruct(
                    id=str(uuid.uuid4()), 
                    vector=vector,
                    payload=meta
                )
            )

        self.client.upsert(
            collection_name=self.collection,
            points=points
        )