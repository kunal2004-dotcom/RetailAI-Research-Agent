from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
from backend.app.models.base import Base, get_utc_now

class Finding(Base):
    __tablename__ = "findings"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("research_sessions.id"), nullable=False, index=True)
    statement = Column(String, nullable=False)
    confidence = Column(Float, nullable=True)
    created_at = Column(DateTime, default=get_utc_now, index=True)

    session = relationship("ResearchSession", back_populates="findings")
    evidence_links = relationship("FindingEvidence", back_populates="finding")


class FindingEvidence(Base):
    __tablename__ = "finding_evidence"

    id = Column(Integer, primary_key=True, index=True)
    finding_id = Column(Integer, ForeignKey("findings.id"), nullable=False, index=True)
    evidence_id = Column(Integer, ForeignKey("evidence_items.id"), nullable=False, index=True)
    relationship_type = Column(String, nullable=False) # supports, contradicts

    finding = relationship("Finding", back_populates="evidence_links")
    evidence = relationship("EvidenceItem", back_populates="finding_links")
