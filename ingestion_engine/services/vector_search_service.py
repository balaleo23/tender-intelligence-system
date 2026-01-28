from qdrant_client import QdrantClient
from ingestion_engine.services.embedding_service import EmbeddingService

# from dotenv import load_dotenv
# from openai import OpenAI
# import os
# load_dotenv()

# client = OpenAI()


class VectorSearchService:

    def __init__(self):
        self.qdrant = QdrantClient(host="localhost", port=6333)
        self.collection = "tenders"
        self.embedder = EmbeddingService()

    def search(self, query: str, top_k: int = 5):
        query_vector = self.embedder.embed_query(query)
        # query_vector = self.embedder.embed_query([query])[0]

        results = self.qdrant.query_points(
            collection_name=self.collection,
            query=query_vector,
            limit=top_k
        )

        return results.points


# class VectorSearchService:

#     def __init__(self):
#         self.qdrant = QdrantClient(host="localhost", port=6333)
#         self.collection = "tenders"

#     def embed_query(self, query: str) -> list[float]:
#         response = client.embeddings.create(
#             model="text-embedding-3-small",
#             input=query
#         )
#         return response.data[0].embedding

#     def search(self, query: str, top_k: int = 5):
#         query_vector = self.embed_query(query)

#         results = self.qdrant.search(
#             collection_name=self.collection,
#             query_vector=query_vector,
#             limit=top_k
#         )

#         return results
