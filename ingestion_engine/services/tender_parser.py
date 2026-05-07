from datetime import datetime
from typing import Optional

from ingestion_engine.constants import TENDER_DATE_FORMAT, UID_PATTERN


class TenderParser:

    @staticmethod
    def extract_uid(title_ref: str) -> str:
        brackets = UID_PATTERN.findall(title_ref)
        if not brackets:
            raise ValueError(f"No bracketed UID found in: {title_ref!r}")
        return brackets[-1]

    @staticmethod
    def parse_title(title_ref: str) -> str:
        return title_ref.split("]")[0].replace("[", "").strip()

    @staticmethod
    def parse_date(date_str: Optional[str]) -> Optional[datetime]:
        if not date_str:
            return None
        return datetime.strptime(date_str, TENDER_DATE_FORMAT)
