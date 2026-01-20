import os
import hashlib
from sqlalchemy.orm import Session
from ingestion_engine.storage.models import TenderDocument
from pathlib import Path

class DocumentService:

    @staticmethod
    def calculate_checksum(file_path: str) -> str:
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"{file_path} does not exist")

        if not file_path.is_file():
            raise ValueError(f"{file_path} is not a file")

        try:
            hash_md5 = hashlib.md5()
            with file_path.open("rb") as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()

        except PermissionError as e:
            raise PermissionError(
                f"Permission denied while reading file: {file_path}. "
                f"Is it open or locked by another process?"
            ) from e

    # @staticmethod
    # def calculate_checksum(file_path: str) -> str:
    #     file_path = Path(file_path)
        
    #     if not file_path.exists():
    #         raise FileNotFoundError(f"{file_path} does not exist")
    #     if not file_path.is_file():
    #         raise IsADirectoryError(f"{file_path} is a directory, not a file")
        
    #     # calculate MD5 checksum (example)
    #     hash_md5 = hashlib.md5()
    #     with file_path.open("rb") as f:
    #         for chunk in iter(lambda: f.read(4096), b""):
    #             hash_md5.update(chunk)
    #     return hash_md5.hexdigest()
    # @staticmethod
    # def calculate_checksum(file_path: str) -> str:
    #     sha256 = hashlib.sha256()
    #     if file_path:
    #         with open(file_path, "rb") as f:
    #             for chunk in iter(lambda: f.read(8192), b""):
    #                 sha256.update(chunk)
    #         return sha256.hexdigest()
    #     else:
    #         print(file_path)

    @staticmethod
    def register_document(session, tender_id: int, file_path: str):
        file_path = Path(file_path)

        if not file_path.is_file():
            raise ValueError(f"Expected file, got {file_path}")

        checksum = DocumentService.calculate_checksum(file_path)

        document = TenderDocument(
            tender_id=tender_id,
            file_name=file_path.name,
            file_type=file_path.suffix,
            file_size=file_path.stat().st_size,
            storage_path=str(file_path),
            checksum=checksum,
        )

        session.add(document)
        session.flush()
        return document