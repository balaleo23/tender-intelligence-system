from openai import OpenAI

client = OpenAI()


def embed(chunks: list[str]) -> list[list[float]]:
        response = client.embeddings.create(
            model="text-embedding-3-small",
            input=chunks
        )
        return [r.embedding for r in response.data]