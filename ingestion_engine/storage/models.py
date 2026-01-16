from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    ForeignKey,
    UniqueConstraint,
    Index
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class Organization(Base):
    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    parent_id = Column(Integer, ForeignKey("organizations.id"))

    parent = relationship("Organization", remote_side=[id])
    created_at = Column(DateTime, default=datetime.utcnow)


class Tender(Base):
    __tablename__ = "tenders"

    id = Column(Integer, primary_key=True)

    tender_uid = Column(String(100), nullable=False, unique=True)
    title = Column(Text, nullable=False)
    reference_number = Column(String(255), nullable=True)

    published_date = Column(DateTime, nullable=False)
    bid_submission_end_date = Column(DateTime, nullable=False)
    tender_opening_date = Column(DateTime, nullable=True)

    organization_id = Column(Integer, ForeignKey("organizations.id"))
    organization = relationship("Organization")

    source_portal = Column(String(50), default="eprocure.gov.in")
    source_url = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("idx_tender_dates", "published_date", "bid_submission_end_date"),
    )


class TenderDocument(Base):
    __tablename__ = "tender_documents"

    id = Column(Integer, primary_key=True)
    tender_id = Column(Integer, ForeignKey("tenders.id"), nullable=False)

    document_name = Column(String(255))
    document_url = Column(Text)
    local_path = Column(Text)

    created_at = Column(DateTime, default=datetime.utcnow)

    tender = relationship("Tender", backref="documents")


class TenderIngestionLog(Base):
    __tablename__ = "tender_ingestion_logs"

    id = Column(Integer, primary_key=True)
    tender_uid = Column(String(100), nullable=False)

    status = Column(String(50))  # SUCCESS, FAILED
    error_message = Column(Text)

    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_ingestion_status", "tender_uid", "status"),
    )
