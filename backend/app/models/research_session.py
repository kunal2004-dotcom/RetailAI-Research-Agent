from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from backend.app.models.base import Base, get_utc_now

class ResearchSession(Base):
    __tablename__ = "research_sessions"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), index=True)
    research_question = Column(String, nullable=False)
    status = Column(String, default="pending", index=True)
    created_at = Column(DateTime, default=get_utc_now, index=True)
    completed_at = Column(DateTime, nullable=True)
    error_message = Column(String, nullable=True)

    organization = relationship("Organization", back_populates="sessions")
    sources = relationship("Source", back_populates="session")
    evidence = relationship("EvidenceItem", back_populates="session")
    findings = relationship("Finding", back_populates="session")
    recommendations = relationship("Recommendation", back_populates="session")
    workflow_logs = relationship("WorkflowLog", back_populates="session")
