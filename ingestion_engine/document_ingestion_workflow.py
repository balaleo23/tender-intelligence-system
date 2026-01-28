from pathlib import Path

from ingestion_engine.services.extraction_service import ExtractionService
from ingestion_engine.services.document_service import DocumentService
from ingestion_engine.services.chunking_service import ChunkingService
from ingestion_engine.services.embedding_service import EmbeddingService
from ingestion_engine.services.vector_index_service import VectorIndexService
from .utils.file_manager_dir  import storage_manager

def ingest_tender_documents(tender):
    # dirs = get_tender_dirs(tender.tender_uid)
    print("Calling the tender_Documnent")
    # dirs = find_tender_dirs(tender.tender_uid)
    dirs = storage_manager.get_dirs(tender_uid=tender.tender_uid)
    print(tender.tender_uid)
    print(dirs)

    if not dirs:
        return
    
    raw_dir = dirs.get("raw")

    if not raw_dir or not raw_dir.exists():
        print(f"[WARN] Raw dir missing for tender {tender.tender_uid}")
        return
    
    raw_files = list(raw_dir.iterdir())

    if not raw_files:
        print(f"[INFO] No raw files for tender {tender.tender_uid}")
        return
   

    index = VectorIndexService()
    embedding_service = EmbeddingService()

    # STEP 1: handle raw files
    for raw_file in raw_files:

        if raw_file.suffix == ".zip":
            extracted_files = ExtractionService.extract_zip(
                raw_file, dirs["extracted"]
            )
        else:
            extracted_files = [raw_file]

        # STEP 2: process extracted files
        for file_path in extracted_files:
            if not file_path.is_file():
                continue

            text = DocumentService.extract_text(file_path)

            print("---- EXTRACTED TEXT SAMPLE ----")
            print(text[:500])
            print("--------------------------------")

            if len(text.strip()) < 200:
                print(f"[WARN] Very little text extracted from {file_path}")
            if not text.strip():
                continue

            chunks = ChunkingService.chunk_text(text)

            if not chunks:
                continue
            
            vectors = embedding_service.embed_documents(chunks)

            metadatas = []
            for i, chunk in enumerate(chunks):
                metadatas.append({
                    "chunk_index": i,
                    "document": file_path.name,
                    "organization": tender.organization.name if tender.organization else None,
                    "published_date": str(tender.published_date),
                    "tender_uid": tender.tender_uid,
                    "source": "pdf",
                    "text": chunk
                })
            print(metadatas)
            index.upsert(vectors, metadatas)
