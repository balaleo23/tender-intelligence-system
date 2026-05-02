from qdrant_client import QdrantClient
from ollama import chat, ChatResponse

from ingestion_engine.config import settings
from ingestion_engine.services.embedding_service import EmbeddingService
from ingestion_engine.services.vector_search_service import VectorSearchService


def ask_chatbot_structured(question: str, searcher: VectorSearchService) -> dict:
    results = searcher.search(question)

    if not results:
        return {
            "answer": "No relevant tenders found.",
            "citations": [],
            "confidence": 0.0,
        }

    context_blocks = []
    citations = set()

    for r in results:
        payload = r.payload
        context_blocks.append(
            f"""
            Tender ID: {payload["tender_uid"]}
            Document: {payload.get("document", "")}
            Text:
            {payload["text"]}
            """.strip()
        )
        citations.add(payload["tender_uid"])

    context = "\n\n".join(context_blocks)

    messages = [
        {
            "role": "system",
            "content": (
                "You are a Tender Intelligence Assistant.\n"
                "Answer ONLY using the provided context.\n"
                "If the answer is not present, say:\n"
                "'Not found in the available tender documents.'"
            ),
        },
        {
            "role": "user",
            "content": f"Context:\n{context}\n\nQuestion:\n{question}",
        },
    ]

    response: ChatResponse = chat(
        model=settings.ollama_model,
        messages=messages,
    )

    confidence = min(1.0, sum(r.score for r in results) / len(results))

    return {
        "answer": response.message.content,
        "citations": list(citations),
        "confidence": round(confidence, 2),
    }
