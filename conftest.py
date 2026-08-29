import os
import pytest

@pytest.fixture(autouse=True, scope="session")
def set_test_env_vars():
    os.environ["OPENAI_API_KEY"] = "dummy"
    
    # Also reload settings so it picks up the dummy key during tests!
    from backend.app.core.config import settings
    settings.openai_api_key = "dummy"
