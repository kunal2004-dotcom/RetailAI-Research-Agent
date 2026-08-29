import pytest
import uuid
from backend.app.retrieval.interfaces import EmbeddingProvider, VectorStore
from backend.app.retrieval.embeddings import DummyEmbeddings
from backend.app.retrieval.chroma_client import ChromaVectorStore
from backend.app.retrieval.ingestion import DocumentIngestionPipeline, Retriever
import chromadb
from backend.app.core.config import settings

@pytest.fixture(autouse=True)
def override_chroma_settings(monkeypatch):
    monkeypatch.setattr(settings, "use_ephemeral_chroma", True)
    monkeypatch.setattr(settings, "chunk_size", 50)
    monkeypatch.setattr(settings, "chunk_overlap", 10)
    monkeypatch.setattr(settings, "chroma_collection_name", f"test_col_{uuid.uuid4().hex}")

def test_document_ingestion_and_retrieval():
    embedding_provider = DummyEmbeddings()
    vstore = ChromaVectorStore(embedding_provider=embedding_provider)
    pipeline = DocumentIngestionPipeline(vector_store=vstore)
    
    mock_sources = [
        {
            "temp_id": "src_0",
            "title": "Retail Trends 2026",
            "url": "https://example.com/retail",
            "content": "AI is significantly changing retail. Chatbots improve customer service. Inventory management is automated.",
            "retrieved_at": "2026-08-28T00:00:00Z"
        }
    ]
    
    pipeline.ingest_sources(mock_sources, session_id=1)
    
    # Should have split the text into chunks and stored them
    # Now retrieve
    retriever = Retriever(vector_store=vstore)
    results = retriever.retrieve("What is changing retail?", top_k=2, threshold=0.0)
    
    assert len(results) > 0
    assert "content" in results[0]
    assert results[0]["metadata"]["source_temp_id"] == "src_0"
    assert results[0]["metadata"]["session_id"] == 1
    
def test_retrieval_empty_result():
    embedding_provider = DummyEmbeddings()
    vstore = ChromaVectorStore(embedding_provider=embedding_provider)
    # Don't ingest anything
    
    retriever = Retriever(vector_store=vstore)
    results = retriever.retrieve("What is changing retail?", top_k=2, threshold=0.0)
    
    assert len(results) == 0

def test_metadata_preservation():
    embedding_provider = DummyEmbeddings()
    vstore = ChromaVectorStore(embedding_provider=embedding_provider)
    pipeline = DocumentIngestionPipeline(vector_store=vstore)
    
    mock_sources = [
        {
            "temp_id": "src_99",
            "title": "Specific Doc",
            "url": "https://example.com/specific",
            "content": "Specific content.",
            "retrieved_at": "2026-08-28T00:00:00Z"
        }
    ]
    
    pipeline.ingest_sources(mock_sources, session_id=5)
    
    retriever = Retriever(vector_store=vstore)
    results = retriever.retrieve("Specific", top_k=1, threshold=0.0)
    
    assert len(results) == 1
    meta = results[0]["metadata"]
    assert meta["source_temp_id"] == "src_99"
    assert meta["source_url"] == "https://example.com/specific"
    assert meta["document_title"] == "Specific Doc"
    assert meta["session_id"] == 5
