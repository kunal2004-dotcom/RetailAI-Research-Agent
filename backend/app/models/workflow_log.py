from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from backend.app.models.base import Base, get_utc_now

class WorkflowLog(Base):
    __tablename__ = "workflow_logs"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("research_sessions.id"), nullable=False, index=True)
    node_name = Column(String, nullable=False, index=True)
    status = Column(String, nullable=False, index=True)
    input_summary = Column(String)
    output_summary = Column(String)
    started_at = Column(DateTime, default=get_utc_now)
    completed_at = Column(DateTime, nullable=True)
    error_message = Column(String, nullable=True)

    session = relationship("ResearchSession", back_populates="workflow_logs")
