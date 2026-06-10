from qdrant_client import QdrantClient

from ingestion_engine.config import settings
from ingestion_engine.services.embedding_service import EmbeddingService
from ingestion_engine.services.vector_search_service import VectorSearchService

client = QdrantClient(host=settings.qdrant_host, port=settings.qdrant_port)
embedder = EmbeddingService()
searcher = VectorSearchService(client=client, embedder=embedder)

question = "Repair and maintenance tenders in Delhi"

results = searcher.search(question, top_k=5)

print("\n🔍 Retrieved Chunks:\n")

for r in results:
    payload = r.payload
    print("Score:", r.score)
    print(r.payload["text"][:300])
    print("Tender:", payload.get("tender_uid"))
    print("Document:", payload.get("document"))
    print("-" * 50)
