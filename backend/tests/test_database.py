import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.app.models.base import Base
from backend.app.models.organization import Organization
from backend.app.models.research_session import ResearchSession
from backend.app.models.source import Source
from backend.app.models.evidence import EvidenceItem
from backend.app.models.finding import Finding, FindingEvidence
from backend.app.models.recommendation import Recommendation

from sqlalchemy.pool import StaticPool

# Use in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db_session():
    # Create tables
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    yield db
    # Drop tables after test
    db.close()
    Base.metadata.drop_all(bind=engine)

def test_create_tables_and_relations(db_session):
    # 1. Test Organization creation
    org = Organization(name="Retail Corp", industry="Retail")
    db_session.add(org)
    db_session.commit()
    db_session.refresh(org)
    
    assert org.id is not None
    assert org.name == "Retail Corp"
    
    # 2. Test ResearchSession creation
    session = ResearchSession(
        organization_id=org.id,
        research_question="What are the latest AI trends in retail?",
        status="running"
    )
    db_session.add(session)
    db_session.commit()
    db_session.refresh(session)
    
    assert session.id is not None
    assert session.organization_id == org.id
    assert session.status == "running"
    
    # 3. Test Source creation
    source = Source(
        session_id=session.id,
        title="AI in Retail 2026",
        url="https://example.com/ai-retail",
        source_type="article"
    )
    db_session.add(source)
    db_session.commit()
    db_session.refresh(source)
    
    assert source.id is not None
    assert source.session_id == session.id
    
    # 4. Test Evidence creation
    evidence = EvidenceItem(
        source_id=source.id,
        session_id=session.id,
        text="Retailers are investing heavily in AI for personalized recommendations.",
        evidence_type="quote",
        relevance_score=0.95
    )
    db_session.add(evidence)
    db_session.commit()
    db_session.refresh(evidence)
    
    assert evidence.id is not None
    assert evidence.source_id == source.id
    
    # 5. Test Finding and FindingEvidence creation
    finding = Finding(
        session_id=session.id,
        statement="Personalized recommendations are a top investment area.",
        confidence=0.9
    )
    db_session.add(finding)
    db_session.commit()
    db_session.refresh(finding)
    
    finding_evidence = FindingEvidence(
        finding_id=finding.id,
        evidence_id=evidence.id,
        relationship_type="supports"
    )
    db_session.add(finding_evidence)
    db_session.commit()
    db_session.refresh(finding_evidence)
    
    assert finding.id is not None
    assert finding_evidence.id is not None
    assert finding_evidence.relationship_type == "supports"
    
    # 6. Test Recommendation creation
    recommendation = Recommendation(
        session_id=session.id,
        recommendation="Invest in personalized AI engines.",
        rationale="Strong evidence suggests competitors are prioritizing this.",
        confidence=0.88
    )
    db_session.add(recommendation)
    db_session.commit()
    db_session.refresh(recommendation)
    
    assert recommendation.id is not None
    assert recommendation.session_id == session.id

    # 7. Check relationship traversal (Traceability)
    assert len(org.sessions) == 1
    assert org.sessions[0].id == session.id
    
    assert len(session.sources) == 1
    assert session.sources[0].id == source.id
    
    assert len(source.evidence) == 1
    assert source.evidence[0].id == evidence.id
    
    assert len(session.findings) == 1
    assert session.findings[0].id == finding.id
    
    # Check finding -> evidence link
    assert len(finding.evidence_links) == 1
    assert finding.evidence_links[0].evidence.text == "Retailers are investing heavily in AI for personalized recommendations."
    
    assert len(session.recommendations) == 1
    assert session.recommendations[0].id == recommendation.id
