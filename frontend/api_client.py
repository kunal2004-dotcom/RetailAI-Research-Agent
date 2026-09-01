import os
import time
import httpx
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

BACKEND_API_URL = os.getenv("BACKEND_API_URL", "http://localhost:8000")

class APIClient:
    def __init__(self, base_url: str = BACKEND_API_URL):
        self.base_url = base_url.rstrip("/")
        
    def _request_with_retry(self, method: str, url: str, **kwargs) -> httpx.Response:
        max_retries = 12
        delay = 5.0
        last_exception = None
        
        for attempt in range(max_retries):
            try:
                response = httpx.request(method, url, **kwargs)
                if response.status_code in [502, 503, 504]:
                    if attempt < max_retries - 1:
                        time.sleep(delay)
                        continue
                response.raise_for_status()
                return response
            except (httpx.ConnectError, httpx.ReadTimeout, httpx.ConnectTimeout) as e:
                last_exception = e
                if attempt < max_retries - 1:
                    time.sleep(delay)
                    continue
                raise e
            except httpx.HTTPStatusError as e:
                # If it's not a 502/503/504, raise it immediately (e.g. 422 validation error)
                raise e
                
        if last_exception:
            raise last_exception
        raise Exception("Backend is unavailable or timed out.")

    def check_health(self) -> bool:
        try:
            response = self._request_with_retry("GET", f"{self.base_url}/health", timeout=10.0)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False

    def create_research_session(self, question: str) -> Dict[str, Any]:
        try:
            response = self._request_with_retry(
                "POST",
                f"{self.base_url}/api/research",
                json={"question": question},
                timeout=30.0
            )
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error occurred: {e}")
            msg = e.response.text
            if "<html" in msg.lower():
                msg = f"Proxy error {e.response.status_code}"
            raise Exception(f"Failed to create session: {msg}")
        except Exception as e:
            logger.error(f"Error creating session: {e}")
            raise Exception("Backend is unavailable or timed out while waking up.")

    def get_research_session(self, session_id: int) -> Dict[str, Any]:
        try:
            response = self._request_with_retry("GET", f"{self.base_url}/api/research/{session_id}", timeout=30.0)
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error occurred: {e}")
            raise Exception(f"Failed to fetch session details: {e.response.status_code}")
        except Exception as e:
            logger.error(f"Error fetching session: {e}")
            raise Exception("Backend is unavailable or timed out.")

    def get_research_sessions(self, skip: int = 0, limit: int = 20) -> List[Dict[str, Any]]:
        try:
            response = self._request_with_retry(
                "GET",
                f"{self.base_url}/api/research",
                params={"skip": skip, "limit": limit},
                timeout=30.0
            )
            return response.json()
        except Exception as e:
            logger.error(f"Error fetching sessions list: {e}")
            return []

    def delete_session(self, session_id: int) -> bool:
        try:
            response = self._request_with_retry("DELETE", f"{self.base_url}/api/research/{session_id}", timeout=30.0)
            return True
        except Exception as e:
            logger.error(f"Error deleting session {session_id}: {e}")
            return False
