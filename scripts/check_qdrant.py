from qdrant_client import QdrantClient
c = QdrantClient(host='localhost', port=6333)
print('Qdrant OK:', c.get_collections())    