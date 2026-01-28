from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance

# Connect to Qdrant
client = QdrantClient(host="localhost", port=6333)
client.delete_collection("tenders")
COLLECTION_NAME = "tenders"
VECTOR_SIZE = 384  # IMPORTANT: must match embedding dimension

# Check if collection exists
existing = [c.name for c in client.get_collections().collections]

if COLLECTION_NAME not in existing:
    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(
            size=VECTOR_SIZE,
            distance=Distance.COSINE
        )
    )
    print(f"Collection '{COLLECTION_NAME}' created")
else:
    print(f"Collection '{COLLECTION_NAME}' already exists")
