from typing import TypedDict, List, Dict, Any, Optional

class ResearchState(TypedDict):
    session_id: int
    research_question: str
    search_queries: List[str]
    sources: List[Dict[str, Any]]
    retrieved_chunks: List[Dict[str, Any]]
    evidence: List[Dict[str, Any]]
    findings: List[Dict[str, Any]]
    recommendations: List[Dict[str, Any]]
    errors: List[str]
    current_step: str
