from fastapi import APIRouter, Depends

from ingestion_engine.api.dependencies import get_searcher
from ingestion_engine.api.schemas import QueryRequest, QueryResponse
from ingestion_engine.chatbot import ask_chatbot_structured
from ingestion_engine.services.vector_search_service import VectorSearchService

router = APIRouter()


@router.post("/query", response_model=QueryResponse)
def query(request: QueryRequest, searcher: VectorSearchService = Depends(get_searcher)) -> QueryResponse:
    result = ask_chatbot_structured(request.question, searcher)
    return QueryResponse(**result)
