import json
from pathlib import Path

from qdrant_client import QdrantClient

from ingestion_engine.config import settings
from ingestion_engine.utils.logger import get_logger

logger = get_logger(__name__)
from ingestion_engine.storage.postgres import get_session
from ingestion_engine.storage.models import Tender
from ingestion_engine.services.tender_repository import TenderRepository
from ingestion_engine.services.document_service import DocumentService
from ingestion_engine.services.chunking_service import ChunkingService
from ingestion_engine.services.embedding_service import EmbeddingService
from ingestion_engine.services.vector_index_service import VectorIndexService
from ingestion_engine.document_ingestion_workflow import ingest_tender_documents


def load_metadata(folder: Path) -> tuple[list, list]:
    records, filerecords = [], []
    for json_file in folder.glob("*.json"):
        with open(json_file, "rb") as f:
            if "Tender_data" in json_file.name:
                records = json.load(f)
            elif "Tenders_filepath" in json_file.name:
                filerecords = json.load(f)
    return records, filerecords


def run_pipeline():
    records, filerecords = load_metadata(Path("meta_data"))

    if not records:
        logger.error("No Tender_data JSON found in meta_data/")
        return

    # Build shared services once — not inside every loop iteration
    qdrant_client = QdrantClient(host=settings.qdrant_host, port=settings.qdrant_port)
    embedding_service = EmbeddingService()
    chunker = ChunkingService()
    index = VectorIndexService(client=qdrant_client)

    tender_id_map = {}

    with get_session() as session:
        for record in records:
            tender = TenderRepository.create_from_json(session, record)
            tender_id_map[tender.tender_uid] = tender.id

    with get_session() as session:
        for filerecord in filerecords:
            for uid, path in filerecord.items():
                if uid in tender_id_map:
                    DocumentService.register_document(session, tender_id_map[uid], path)

    with get_session() as session:
        for uid in tender_id_map:
            tender = session.query(Tender).filter_by(tender_uid=uid).one()
            ingest_tender_documents(tender, index=index, embedding_service=embedding_service, chunker=chunker)


if __name__ == "__main__":
    run_pipeline()
