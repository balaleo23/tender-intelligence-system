from ollama import chat, ChatResponse

from ingestion_engine.config import settings
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
            f"Tender ID: {payload['tender_uid']}\n"
            f"Organisation: {payload.get('organization', 'N/A')}\n"
            f"Published: {payload.get('published_date', 'N/A')}\n"
            f"Document: {payload.get('document', '')}\n"
            f"Text:\n{payload['text']}"
        )
        citations.add(payload["tender_uid"])

    context = "\n\n---\n\n".join(context_blocks)

    messages = [
        {
            "role": "system",
            "content": (
                "You are a Tender Intelligence Assistant.\n"
                "Answer ONLY using the provided context.\n"
                "Include tender IDs, organisations, and dates in your answer when relevant.\n"
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

    # Top result score — best chunk relevance is more meaningful than average
    confidence = round(results[0].score, 2)

    return {
        "answer": response.message.content,
        "citations": list(citations),
        "confidence": confidence,
    }
