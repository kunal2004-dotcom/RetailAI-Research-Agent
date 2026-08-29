import pytest
from unittest.mock import patch, MagicMock
from backend.app.ai.state import ResearchState
from backend.app.ai.workflow import research_graph
from backend.app.services.research_service import ResearchService
from backend.app.models.research_session import ResearchSession
from backend.app.models.source import Source
from backend.app.models.evidence import EvidenceItem
from backend.app.models.finding import Finding
from backend.app.models.recommendation import Recommendation
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from backend.app.models import Base

# Test database setup (in-memory SQLite)
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(autouse=True)
def create_test_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def db_session():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

def test_workflow_initialization_and_mocked_execution():
    # Because we don't have OPENAI_API_KEY set, our fallback logic in the nodes will execute.
    # We can test that the fallback logic successfully creates mock data and traverses the graph.
    state = {
        "session_id": 1,
        "research_question": "What is AI?",
        "search_queries": [],
        "sources": [],
        "evidence": [],
        "findings": [],
        "recommendations": [],
        "errors": [],
        "current_step": "init"
    }

    final_state = research_graph.invoke(state)
    
    assert final_state["current_step"] == "recommendations"
    assert len(final_state["search_queries"]) > 0
    assert len(final_state["sources"]) > 0
    assert len(final_state["evidence"]) > 0
    assert len(final_state["findings"]) > 0
    assert len(final_state["recommendations"]) > 0
    
    source_ids = {s["temp_id"] for s in final_state["sources"]}
    assert all(ev["source_temp_id"] in source_ids for ev in final_state["evidence"])
    
    linked_ev_id = final_state["findings"][0]["evidence_links"][0]["evidence_temp_id"]
    assert any(ev["temp_id"] == linked_ev_id for ev in final_state["evidence"])

def test_research_service_execute_workflow(db_session):
    # Test DB persistence using fallback workflow
    session = ResearchSession(research_question="What is retail AI?", status="pending")
    db_session.add(session)
    db_session.commit()
    db_session.refresh(session)
    
    ResearchService.execute_workflow(db_session, session.id)
    
    db_session.refresh(session)
    assert session.status == "completed"
    
    sources = db_session.query(Source).filter(Source.session_id == session.id).all()
    assert len(sources) > 0
    
    evidence = db_session.query(EvidenceItem).filter(EvidenceItem.session_id == session.id).all()
    assert len(evidence) > 0
    
    findings = db_session.query(Finding).filter(Finding.session_id == session.id).all()
    assert len(findings) > 0
    
    recs = db_session.query(Recommendation).filter(Recommendation.session_id == session.id).all()
    assert len(recs) > 0
