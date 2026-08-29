import pytest
from unittest.mock import patch, MagicMock
import httpx
from frontend.api_client import APIClient

@pytest.fixture
def client():
    return APIClient(base_url="http://mocked-backend:8000")

def test_check_health_success(client):
    with patch("httpx.get") as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        assert client.check_health() is True

def test_check_health_failure(client):
    with patch("httpx.get") as mock_get:
        mock_get.side_effect = httpx.RequestError("Failed")
        assert client.check_health() is False

def test_create_research_session_success(client):
    with patch("httpx.post") as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"id": 1, "status": "pending"}
        mock_post.return_value = mock_response
        
        result = client.create_research_session("Test question")
        assert result["id"] == 1
        assert result["status"] == "pending"

def test_create_research_session_error(client):
    with patch("httpx.post") as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError("500", request=MagicMock(), response=mock_response)
        mock_post.return_value = mock_response
        
        with pytest.raises(Exception, match="Failed to create session"):
            client.create_research_session("Test question")

def test_get_research_session_success(client):
    with patch("httpx.get") as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": 1, "status": "completed", "findings": []}
        mock_get.return_value = mock_response
        
        result = client.get_research_session(1)
        assert result["id"] == 1
        assert result["status"] == "completed"

def test_get_research_sessions_empty(client):
    with patch("httpx.get") as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = []
        mock_get.return_value = mock_response
        
        result = client.get_research_sessions()
        assert len(result) == 0
