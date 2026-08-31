import os
import httpx
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

BACKEND_API_URL = os.getenv("BACKEND_API_URL", "http://localhost:8000")

class APIClient:
    def __init__(self, base_url: str = BACKEND_API_URL):
        self.base_url = base_url.rstrip("/")
        
    def check_health(self) -> bool:
        try:
            response = httpx.get(f"{self.base_url}/health", timeout=5.0)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False

    def create_research_session(self, question: str) -> Dict[str, Any]:
        try:
            response = httpx.post(
                f"{self.base_url}/api/research",
                json={"question": question},
                timeout=60.0
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error occurred: {e}")
            raise Exception(f"Failed to create session: {e.response.text}")
        except Exception as e:
            logger.error(f"Error creating session: {e}")
            raise Exception("Backend is unavailable or timed out.")

    def get_research_session(self, session_id: int) -> Dict[str, Any]:
        try:
            response = httpx.get(f"{self.base_url}/api/research/{session_id}", timeout=60.0)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error occurred: {e}")
            raise Exception(f"Failed to fetch session details: {e.response.status_code}")
        except Exception as e:
            logger.error(f"Error fetching session: {e}")
            raise Exception("Backend is unavailable or timed out.")

    def get_research_sessions(self, skip: int = 0, limit: int = 20) -> List[Dict[str, Any]]:
        try:
            response = httpx.get(
                f"{self.base_url}/api/research",
                params={"skip": skip, "limit": limit},
                timeout=60.0
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error fetching sessions list: {e}")
            return []

    def delete_session(self, session_id: int) -> bool:
        try:
            response = httpx.delete(f"{self.base_url}/api/research/{session_id}", timeout=60.0)
            response.raise_for_status()
            return True
        except Exception as e:
            logger.error(f"Error deleting session {session_id}: {e}")
            return False
