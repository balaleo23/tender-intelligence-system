from ingestion_engine.constants import SOURCE_PORTAL
from ingestion_engine.storage.models import Organization, Tender
from ingestion_engine.services.tender_parser import TenderParser


class TenderBuilder:

    @staticmethod
    def build(record: dict, organization: Organization) -> Tender:
        title_ref = record["Title and Ref.No./Tender ID"]

        return Tender(
            tender_uid=TenderParser.extract_uid(title_ref),
            title=TenderParser.parse_title(title_ref),
            published_date=TenderParser.parse_date(record["e-Published Date"]),
            bid_submission_end_date=TenderParser.parse_date(record["Bid Submission Closing Date"]),
            tender_opening_date=TenderParser.parse_date(record.get("Tender Opening Date")),
            organization=organization,
            source_portal=SOURCE_PORTAL,
        )
