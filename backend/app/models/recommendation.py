from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
from backend.app.models.base import Base, get_utc_now

class Recommendation(Base):
    __tablename__ = "recommendations"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("research_sessions.id"), nullable=False, index=True)
    recommendation = Column(String, nullable=False)
    rationale = Column(String)
    confidence = Column(Float, nullable=True)
    created_at = Column(DateTime, default=get_utc_now, index=True)

    session = relationship("ResearchSession", back_populates="recommendations")
