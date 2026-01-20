from sqlalchemy.orm import Session
from ingestion_engine.storage.models import Organization
from ingestion_engine.storage.models import Tender
import re
from datetime import datetime

from ingestion_engine.storage.services.organization_service import OrganizationService

class TenderService:
    """
    Handles tender creation and deduplication
    """
    TENDER_ID_REGEX = r"\[(\d{4}_[A-Z]+_\d+_\d+)\]"
    

    @staticmethod
    def extract_tender_uid(title_ref: str) -> str:
        match = re.search(TenderService.TENDER_ID_REGEX, title_ref)
        if not match:
            raise ValueError("Tender UID not found")
        return match.group(1)
    
    @staticmethod
    def extract_tender_id(title_ref: str) -> str:
        brackets = re.findall(r"\[([^\]]+)\]", title_ref)
        tender_ref = brackets[-2]
        tender_id = brackets[-1]
        if not tender_id:
            raise ValueError("Tender UID not found")
        return tender_id

    @staticmethod
    def extract_title(title_ref: str) -> str:
        return title_ref.split("]")[0].replace("[", "").strip()
    
    @staticmethod
    def parse_date(date_str: str | None) -> datetime | None:
        if not date_str:
            return None
        return datetime.strptime(date_str, "%d-%b-%Y %I:%M %p")
    

    @staticmethod
    def create_from_json(
        session: Session,
        record: dict
    ) -> Tender:
        tender_uid = TenderService.extract_tender_id(
            record["Title and Ref.No./Tender ID"]
        )

        # Deduplication
        existing = (
            session.query(Tender)
            .filter_by(tender_uid=tender_uid)
            .one_or_none()
        )
        if existing:
            return existing

        organization = OrganizationService.get_or_create_chain(
            session,
            record["Organisation Chain"]
        )

        tender = Tender(
            tender_uid=tender_uid,
            title=TenderService.extract_title(
                record["Title and Ref.No./Tender ID"]
            ),
            published_date=TenderService.parse_date(
                record["e-Published Date"]
            ),
            bid_submission_end_date=TenderService.parse_date(
                record["Bid Submission Closing Date"]
            ),
            tender_opening_date=TenderService.parse_date(
                record.get("Tender Opening Date")
            ),
            organization=organization,
            source_portal="eprocure.gov.in"
        )

        session.add(tender)
        session.commit()

        return tender