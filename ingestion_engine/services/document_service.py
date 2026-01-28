import os
import hashlib
from sqlalchemy.orm import Session
from ingestion_engine.storage.models import TenderDocument
from pathlib import Path
from pathlib import Path
from PyPDF2 import PdfReader
from pdf2image import convert_from_path
import pytesseract

class DocumentService:


    @staticmethod
    def extract_text(file_path: Path) -> str:
        
        if file_path.suffix.lower() == ".pdf":
            return DocumentService._extract_pdf(file_path)
        return ""
        
    
    @staticmethod
    def _extract_pdf(file_path: Path) -> str:
        reader = PdfReader(str(file_path))
        text = ""

        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"

        # fallback to OCR
        if len(text.strip()) < 100:
            text = DocumentService._extract_pdf_ocr(file_path)

        return text
    
    @staticmethod
    def _extract_pdf_ocr(file_path: Path) -> str:
        images = convert_from_path(file_path ,dpi=300, poppler_path=r"C:\poppler\poppler-25.12.0\Library\bin")
        ocr_text = ""

        for img in images:
            pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
            ocr_text += pytesseract.image_to_string(img, lang="eng",  config="--psm 6") + "\n"

        return ocr_text

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