import hashlib
from pathlib import Path

from PyPDF2 import PdfReader
from pdf2image import convert_from_path
from sqlalchemy.orm import Session
import pytesseract

from ingestion_engine.config import settings
from ingestion_engine.constants import MIN_TEXT_LENGTH, OCR_DPI, OCR_LANG, TESSERACT_CONFIG, FILE_CHUNK_SIZE
from ingestion_engine.storage.models import TenderDocument


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

        if len(text.strip()) < MIN_TEXT_LENGTH:
            text = DocumentService._extract_pdf_ocr(file_path)

        return text

    @staticmethod
    def _extract_pdf_ocr(file_path: Path) -> str:
        if settings.tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = str(settings.tesseract_cmd)

        images = convert_from_path(
            file_path,
            dpi=OCR_DPI,
            poppler_path=str(settings.poppler_path) if settings.poppler_path else None,
        )
        ocr_text = ""
        for img in images:
            ocr_text += pytesseract.image_to_string(img, lang=OCR_LANG, config=TESSERACT_CONFIG) + "\n"

        return ocr_text

    @staticmethod
    def calculate_checksum(file_path: Path) -> str:
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"{file_path} does not exist")
        if not file_path.is_file():
            raise ValueError(f"{file_path} is not a file")

        try:
            hash_md5 = hashlib.md5()
            with file_path.open("rb") as f:
                for chunk in iter(lambda: f.read(FILE_CHUNK_SIZE), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except PermissionError as e:
            raise PermissionError(
                f"Permission denied reading {file_path} — is it open by another process?"
            ) from e

    @staticmethod
    def register_document(session: Session, tender_id: int, file_path: str) -> TenderDocument:
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
