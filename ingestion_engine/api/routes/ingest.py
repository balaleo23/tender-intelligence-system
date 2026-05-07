import json
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ingestion_engine.api.dependencies import get_db, get_embedder, get_index, get_chunker
from ingestion_engine.api.schemas import IngestResponse
from ingestion_engine.constants import METADATA_DIR
from ingestion_engine.document_ingestion_workflow import ingest_tender_documents
from ingestion_engine.services.chunking_service import ChunkingService
from ingestion_engine.services.document_service import DocumentService
from ingestion_engine.services.embedding_service import EmbeddingService
from ingestion_engine.services.tender_repository import TenderRepository
from ingestion_engine.services.vector_index_service import VectorIndexService
from ingestion_engine.storage.models import Tender

router = APIRouter()


@router.post("/ingest", response_model=IngestResponse)
def ingest(
    db: Session = Depends(get_db),
    index: VectorIndexService = Depends(get_index),
    embedding_service: EmbeddingService = Depends(get_embedder),
    chunker: ChunkingService = Depends(get_chunker),
) -> IngestResponse:
    metadata_path = Path(METADATA_DIR)
    if not metadata_path.exists():
        raise HTTPException(status_code=404, detail=f"Metadata folder '{METADATA_DIR}' not found")

    records, filerecords = [], []
    for json_file in metadata_path.glob("*.json"):
        with open(json_file, "rb") as f:
            if "Tender_data" in json_file.name:
                records = json.load(f)
            elif "Tenders_filepath" in json_file.name:
                filerecords = json.load(f)

    if not records:
        raise HTTPException(status_code=422, detail="No Tender_data JSON found in metadata folder")

    tender_id_map: dict[str, int] = {}

    for record in records:
        tender = TenderRepository.create_from_json(db, record)
        tender_id_map[tender.tender_uid] = tender.id

    for filerecord in filerecords:
        for uid, path in filerecord.items():
            if uid in tender_id_map:
                DocumentService.register_document(db, tender_id_map[uid], path)

    processed = 0
    for uid in tender_id_map:
        tender = db.query(Tender).filter_by(tender_uid=uid).one_or_none()
        if tender:
            ingest_tender_documents(tender, index=index, embedding_service=embedding_service, chunker=chunker)
            processed += 1

    return IngestResponse(message="Ingestion complete", tenders_processed=processed)
