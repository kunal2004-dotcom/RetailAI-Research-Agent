from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
from backend.app.models.base import Base, get_utc_now

class EvidenceItem(Base):
    __tablename__ = "evidence_items"

    id = Column(Integer, primary_key=True, index=True)
    source_id = Column(Integer, ForeignKey("sources.id"), nullable=False, index=True)
    session_id = Column(Integer, ForeignKey("research_sessions.id"), nullable=False, index=True)
    text = Column(String, nullable=False)
    evidence_type = Column(String)
    relevance_score = Column(Float, nullable=True)
    created_at = Column(DateTime, default=get_utc_now, index=True)

    source = relationship("Source", back_populates="evidence")
    session = relationship("ResearchSession", back_populates="evidence")
    finding_links = relationship("FindingEvidence", back_populates="evidence")
