
# from google.genai import types
# from google import genai
# # from ollama import chat
# from ingestion_engine.services.vector_search_service import VectorSearchService
# from ollama import chat, ChatResponse

from ollama import chat, ChatResponse
from ingestion_engine.services.vector_search_service import VectorSearchService

# from dotenv import load_dotenv
# import os


# load_dotenv()

def ask_chatbot_structured(question: str):
    searcher = VectorSearchService()
    results = searcher.search(question, top_k=5)

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
            Tender ID: {payload['tender_uid']}
            Document: {payload.get('document', '')}
            Text:
            {payload['text']}
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
            "content": f"""
Context:
{context}

Question:
{question}
""".strip(),
        },
    ]

    response: ChatResponse = chat(
        model="mistral",   # MUST exist in `ollama list`
        messages=messages,
    )

    confidence = min(1.0, sum(r.score for r in results) / len(results))

    return {
        "answer": response.message.content,
        "citations": list(citations),
        "confidence": round(confidence, 2),
    }

# client = genai.Client()

# def ask_chatbot_structured(question: str):
#     searcher = VectorSearchService()
    

#     results = searcher.search(question, top_k=5)

#     if not results:
#         return {
#             "answer": "No relevant tenders found.",
#             "citations": [],
#             "confidence": 0.0
#         }

#     context_blocks = []
#     citations = set()

#     for r in results:
#         payload = r.payload
#         context_blocks.append(
#             f"""
# Tender ID: {payload['tender_uid']}
# Document: {payload['document']}
# Text:
# {payload['text']}
# """
#         )
#         citations.add(payload["tender_uid"])

#     context = "\n".join(context_blocks)

#     prompt = f"""
# You are a Tender Intelligence Assistant.

# Use ONLY the context below.
# If information is missing, say so.

# Context:
# {context}

# Question:
# {question}
# """
#     response: ChatResponse = chat(
#         model= "gemma3:4b",
#         messages=prompt,
#     )
#     # answer = chat(model="gemma3")

#     confidence = min(1.0, sum(r.score for r in results) / len(results))

#     # return response.message.content

#     return {
#         "answer": response.message.content,
#         "citations": list(citations),
#         "confidence": round(confidence, 2)
#     }

# # def ask_chatbot_structured(question: str):
#     searcher = VectorSearchService()
#     results = searcher.search(question, top_k=5)
#     chat = OllamaChatService("llama3")

#     if not results:
#         return {"answer": "No relevant tenders found in the database.", "citations": [], "confidence": 0}

#     # Build richer context
#     tender_data = []
#     for r in results:
#         payload = r.payload
#         tender_data.append({
#             "tender_uid": payload["tender_uid"],
#             "document": payload.get("document", ""),
#             "relevance_score": round(r.score, 3)
#         })

#     context = "\n".join([
#         f"Tender {t['tender_uid']}: {t['document']} (relevance: {t['relevance_score']})"
#         for t in tender_data
#     ])

#     prompt = f"""
# Analyze the following tender data and answer the question.

# Tender Data:
# {context}

# Question: {question}

# Provide your reasoning, cite specific tender IDs, and rate your confidence.
# """

#     # Define structured output schema
#     schema = {
#         'type': 'object',
#         'properties': {
#             'answer': {'type': 'string', 'description': 'The main answer to the question'},
#             'reasoning': {'type': 'string', 'description': 'Step-by-step reasoning process'},
#             'citations': {
#                 'type': 'array',
#                 'items': {'type': 'string'},
#                 'description': 'List of tender UIDs referenced'
#             },
#             'confidence': {
#                 'type': 'number',
#                 'description': 'Confidence score from 0 to 1'
#             }
#         },
#         'required': ['answer', 'reasoning', 'citations', 'confidence']
#     }

#     result = chat.ask(prompt)
#     # response = client.models.generate_content(
#     #     model="gemini-2.5-flash",
#     #     contents=prompt,
#     #     config={
#     #         'system_instruction': "You are a Tender Intelligence assistant that provides structured, well-reasoned answers.",
#     #         'response_mime_type': 'application/json',
#     #         'response_schema': schema,
#     #         'temperature': 0
#     #     }
#     # )

#     # result = response.parsed  # Automatically parsed JSON
#     return result




# from google import genai
# from ingestion_engine.services.vector_search_service import VectorSearchService
# from dotenv import load_dotenv
# import os

# load_dotenv()



# client = genai.Client()

# def ask_chatbot(question: str):
#     searcher = VectorSearchService()
#     results = searcher.search(question, top_k=5)

#     if not results:
#         return "No relevant tenders found in the database."

#     context = ""
#     citations = set()

#     for r in results:
#         payload = r.payload
#         context += f"- Tender {payload['tender_uid']} ({payload['document']})\n"
#         citations.add(payload["tender_uid"])

#     prompt = f"""
# You are a Tender Intelligence assistant.
# Answer the question ONLY using the context below.
# If the answer is not present, say "Not found in the data".

# Context:
# {context}

# Question:
# {question}
# """

#     response = client.models.generate_content(
#         model="gemini-2.5-flash",
#         messages=[
#             {"role": "system", "content": "You are a helpful assistant."},
#             {"role": "user", "content": prompt}
#         ]
#     )

#     answer = response.choices[0].message.content

#     return answer, citations