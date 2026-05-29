from ingestion_engine.services.extraction_service import ExtractionService
from ingestion_engine.services.document_service import DocumentService
from ingestion_engine.services.chunking_service import ChunkingService
from ingestion_engine.services.embedding_service import EmbeddingService
from ingestion_engine.services.vector_index_service import VectorIndexService
from ingestion_engine.utils.file_manager_dir import storage_manager
from ingestion_engine.utils.logger import get_logger

logger = get_logger(__name__)


def ingest_tender_documents(
    tender,
    index: VectorIndexService,
    embedding_service: EmbeddingService,
    chunker: ChunkingService,
) -> None:
    dirs = storage_manager.get_dirs(tender_uid=tender.tender_uid)

    if not dirs:
        return

    raw_dir = dirs.get("raw")

    if not raw_dir or not raw_dir.exists():
        logger.warning("Raw dir missing for tender %s", tender.tender_uid)
        return

    raw_files = list(raw_dir.iterdir())

    if not raw_files:
        logger.info("No raw files for tender %s", tender.tender_uid)
        return

    for raw_file in raw_files:
        try:
            extracted_files = (
                ExtractionService.extract_zip(raw_file, dirs["extracted"])
                if raw_file.suffix == ".zip"
                else [raw_file]
            )

            for file_path in extracted_files:
                if not file_path.is_file():
                    continue

                if file_path.suffix.lower() in (".xls", ".xlsx", ".xlsm", ".xlsb"):
                    logger.info("Skipping Excel file: %s", file_path.name)
                    continue

                text = DocumentService.extract_text(file_path)

                if not text.strip():
                    logger.warning("No text extracted from %s", file_path.name)
                    continue

                if len(text.strip()) < 200:
                    logger.warning("Very little text extracted from %s", file_path.name)

                chunks = chunker.chunk_text(text)
                if not chunks:
                    continue

                vectors = embedding_service.embed_documents(chunks)

                metadatas = [
                    {
                        "chunk_index": i,
                        "document": file_path.name,
                        "organization": tender.organization.name if tender.organization else None,
                        "published_date": str(tender.published_date),
                        "tender_uid": tender.tender_uid,
                        "source": "pdf",
                        "text": chunk,
                    }
                    for i, chunk in enumerate(chunks)
                ]

                index.upsert(vectors, metadatas)
                logger.info("Upserted %d chunks from %s", len(chunks), file_path.name)

        except Exception as e:
            logger.error("Failed processing %s for tender %s: %s", raw_file.name, tender.tender_uid, e)
            continue
