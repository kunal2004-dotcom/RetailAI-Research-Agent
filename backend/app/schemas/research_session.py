from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class ResearchSessionCreate(BaseModel):
    question: str = Field(..., min_length=5, description="The research question to be answered.")
    organization_id: Optional[int] = None

class ResearchSessionResponse(BaseModel):
    id: int
    organization_id: Optional[int]
    research_question: str
    status: str
    created_at: datetime
    completed_at: Optional[datetime]
    error_message: Optional[str]

class SourceResponse(BaseModel):
    id: int
    title: str
    url: Optional[str] = None
    source_type: Optional[str] = None
    publisher: Optional[str] = None
    
    class Config:
        from_attributes = True

class EvidenceResponse(BaseModel):
    id: int
    source_id: int
    text: str
    evidence_type: Optional[str] = None
    relevance_score: Optional[float] = None
    
    class Config:
        from_attributes = True

class FindingEvidenceResponse(BaseModel):
    evidence_id: int
    relationship_type: str

    class Config:
        from_attributes = True

class FindingResponse(BaseModel):
    id: int
    statement: str
    confidence: Optional[float] = None
    evidence_links: list[FindingEvidenceResponse] = []

    class Config:
        from_attributes = True

class RecommendationResponse(BaseModel):
    id: int
    recommendation: str
    rationale: Optional[str] = None
    confidence: Optional[float] = None

    class Config:
        from_attributes = True

class ResearchSessionDetailResponse(ResearchSessionResponse):
    sources: list[SourceResponse] = []
    evidence: list[EvidenceResponse] = []
    findings: list[FindingResponse] = []
    recommendations: list[RecommendationResponse] = []

    class Config:
        from_attributes = True
