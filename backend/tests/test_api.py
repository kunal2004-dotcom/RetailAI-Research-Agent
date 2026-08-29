import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from unittest.mock import patch

from backend.app.main import app
from backend.app.models.database import get_db
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
def mock_background_tasks():
    with patch("backend.app.api.research.run_workflow_bg"):
        yield

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

@pytest.fixture(autouse=True)
def create_test_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_create_research_session():
    response = client.post(
        "/api/research",
        json={"question": "What is the impact of AI on retail supply chains?"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["research_question"] == "What is the impact of AI on retail supply chains?"
    assert data["status"] == "pending"
    assert "id" in data
    assert "created_at" in data

def test_get_research_session():
    # First create one
    create_response = client.post(
        "/api/research",
        json={"question": "What is the impact of AI on retail supply chains?"}
    )
    session_id = create_response.json()["id"]

    # Now get it
    response = client.get(f"/api/research/{session_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == session_id
    assert data["research_question"] == "What is the impact of AI on retail supply chains?"

def test_get_invalid_research_session():
    response = client.get("/api/research/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Research session not found"

def test_get_research_sessions():
    client.post("/api/research", json={"question": "Question 1"})
    client.post("/api/research", json={"question": "Question 2"})
    
    response = client.get("/api/research?skip=0&limit=10")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2

def test_invalid_research_question():
    # Min length is 5
    response = client.post(
        "/api/research",
        json={"question": "No"}
    )
    assert response.status_code == 422
