from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ingestion_engine.api.dependencies import get_db
from ingestion_engine.api.schemas import TenderResponse
from ingestion_engine.storage.models import Tender

router = APIRouter()


@router.get("/tenders", response_model=list[TenderResponse])
def list_tenders(
    limit: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    organization: Optional[str] = Query(default=None, description="Filter by organization name"),
    db: Session = Depends(get_db),
) -> list[TenderResponse]:
    q = db.query(Tender)

    if organization:
        q = q.filter(Tender.organization.has(name=organization))

    tenders = q.order_by(Tender.published_date.desc()).offset(offset).limit(limit).all()

    return [
        TenderResponse(
            tender_uid=t.tender_uid,
            title=t.title,
            organization=t.organization.name if t.organization else None,
            published_date=t.published_date,
            bid_submission_end_date=t.bid_submission_end_date,
        )
        for t in tenders
    ]
