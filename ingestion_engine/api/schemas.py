from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    postgres: str
    qdrant: str
    ollama: str


class QueryRequest(BaseModel):
    question: str


class QueryResponse(BaseModel):
    answer: str
    citations: list[str]
    confidence: float


class TenderResponse(BaseModel):
    tender_uid: str
    title: str
    organization: Optional[str]
    published_date: datetime
    bid_submission_end_date: datetime

    model_config = {"from_attributes": True}


class IngestResponse(BaseModel):
    message: str
    tenders_processed: int


class ScrapeStatusResponse(BaseModel):
    state: str              # idle | running | done | failed
    tenders_scraped: int
    error: Optional[str]
    started_at: Optional[str]
    finished_at: Optional[str]
    message: str
