from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from backend.app.models.base import Base, get_utc_now

class Organization(Base):
    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    industry = Column(String)
    created_at = Column(DateTime, default=get_utc_now, index=True)

    sessions = relationship("ResearchSession", back_populates="organization")
