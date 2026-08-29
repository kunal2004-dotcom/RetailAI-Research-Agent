from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    
    # LLM Settings
    openai_api_key: str | None = None
    gemini_api_key: str | None = None
    
    # DB Settings
    database_url: str = "sqlite:///./data/sqlite/retailai.db"
    chroma_persist_directory: str = "./data/chroma_db"

    # Retrieval Settings
    top_k: int = 5
    similarity_threshold: float = 0.5
    chunk_size: int = 1000
    chunk_overlap: int = 200
    chroma_collection_name: str = "retail_research"
    use_ephemeral_chroma: bool = False

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
