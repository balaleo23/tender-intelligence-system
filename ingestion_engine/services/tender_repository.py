from sqlalchemy.orm import Session

from ingestion_engine.storage.models import Tender
from ingestion_engine.services.tender_parser import TenderParser
from ingestion_engine.services.tender_builder import TenderBuilder
from ingestion_engine.services.organization_service import OrganizationService


class TenderRepository:

    @staticmethod
    def create_from_json(session: Session, record: dict) -> Tender:
        tender_uid = TenderParser.extract_uid(record["Title and Ref.No./Tender ID"])

        existing = session.query(Tender).filter_by(tender_uid=tender_uid).one_or_none()
        if existing:
            return existing

        organization = OrganizationService.get_or_create_chain(
            session,
            record["Organisation Chain"],
        )

        tender = TenderBuilder.build(record, organization)

        session.add(tender)
        session.commit()

        return tender
