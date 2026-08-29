from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from backend.app.models.base import Base, get_utc_now

class Source(Base):
    __tablename__ = "sources"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("research_sessions.id"), nullable=False, index=True)
    title = Column(String, nullable=False)
    url = Column(String, index=True)
    source_type = Column(String)
    publisher = Column(String)
    published_at = Column(DateTime, nullable=True)
    retrieved_at = Column(DateTime, default=get_utc_now)
    content_hash = Column(String, index=True)
    created_at = Column(DateTime, default=get_utc_now, index=True)

    session = relationship("ResearchSession", back_populates="sources")
    evidence = relationship("EvidenceItem", back_populates="source")

    __table_args__ = (
        UniqueConstraint('session_id', 'url', name='uix_session_url'),
    )
