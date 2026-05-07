from sqlalchemy.orm import Session

from ingestion_engine.constants import ORG_SEPARATOR
from ingestion_engine.storage.models import Organization


class OrganizationService:

    @staticmethod
    def get_or_create_chain(session: Session, org_chain_str: str) -> Organization:
        org_names = [
            name.strip()
            for name in org_chain_str.split(ORG_SEPARATOR)
            if name.strip()
        ]

        parent = None

        for name in org_names:
            org = (
                session.query(Organization)
                .filter_by(name=name, parent=parent)
                .one_or_none()
            )

            if not org:
                org = Organization(name=name, parent=parent)
                session.add(org)
                session.flush()

            parent = org

        return parent
