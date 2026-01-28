# from openai import OpenAI

# client = OpenAI()
from sentence_transformers import SentenceTransformer


class EmbeddingService:

        def __init__(self):
            self.model = SentenceTransformer("BAAI/bge-small-en-v1.5")

        def embed_documents(self, docs: list[str]) -> list[list[float]]:
            docs = [f"Represent this document for retrieval: {d}" for d in docs]
            embeddings = self.model.encode(
                docs,
                normalize_embeddings=True,
                show_progress_bar=False
            )
            return embeddings.tolist()

        def embed_query(self, query: str) -> list[float]:
            query = f"Represent this query for retrieval: {query}"
            embedding = self.model.encode(
                query,
                normalize_embeddings=True,
                show_progress_bar=False
            )
            return embedding.tolist()

# class EmbeddingService:

#     def __init__(self):
#         self.model = SentenceTransformer("BAAI/bge-small-en-v1.5")

#     # @staticmethod
#     def embed(self,chunks: list[str]) -> list[list[float]]:
#         response = self.model.encode(
#             chunks,
#             normalize_embeddings=True,
#             show_progress_bar=False
#         )
#         return response.tolist()
    



# class EmbeddingService:

#     @staticmethod
#     def embed(chunks: list[str]) -> list[list[float]]:
#         response = client.embeddings.create(
#             model="text-embedding-3-small",
#             input=chunks
#         )
#         return [r.embedding for r in response.data]