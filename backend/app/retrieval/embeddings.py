from typing import List
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from backend.app.core.config import settings
from backend.app.retrieval.interfaces import EmbeddingProvider

class BaseGeminiEmbeddings(EmbeddingProvider):
    def __init__(self):
        self.embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-2", google_api_key=settings.gemini_api_key)
        
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return self.embeddings.embed_documents(texts)
        
    def embed_query(self, text: str) -> List[float]:
        return self.embeddings.embed_query(text)

class DummyEmbeddings(EmbeddingProvider):
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [[0.1] * 1536 for _ in texts]
        
    def embed_query(self, text: str) -> List[float]:
        return [0.1] * 1536

def get_embedding_provider() -> EmbeddingProvider:
    if settings.gemini_api_key in ["your_gemini_api_key_here", "dummy"]:
        return DummyEmbeddings()
    return BaseGeminiEmbeddings()
