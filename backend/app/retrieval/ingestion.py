import uuid
import re
from typing import List, Dict, Any
from langchain_text_splitters import RecursiveCharacterTextSplitter
from backend.app.core.config import settings
from backend.app.retrieval.interfaces import VectorStore

class DocumentIngestionPipeline:
    def __init__(self, vector_store: VectorStore):
        self.vector_store = vector_store
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap
        )

    def clean_text(self, text: str) -> str:
        return re.sub(r'\s+', ' ', text).strip()

    def ingest_sources(self, sources: List[Dict[str, Any]], session_id: int):
        documents_to_add = []
        
        for source in sources:
            content = self.clean_text(source.get("content", ""))
            if not content:
                continue
                
            chunks = self.splitter.split_text(content)
            for i, chunk in enumerate(chunks):
                chunk_id = f"{session_id}_{source['temp_id']}_{i}_{uuid.uuid4().hex[:8]}"
                
                metadata = {
                    "source_temp_id": source["temp_id"],
                    "source_url": source.get("url", ""),
                    "document_title": source.get("title", ""),
                    "session_id": session_id,
                    "retrieval_timestamp": source.get("retrieved_at", "")
                }
                
                documents_to_add.append({
                    "id": chunk_id,
                    "content": chunk,
                    "metadata": metadata
                })
                
        self.vector_store.add_documents(documents_to_add)

class Retriever:
    def __init__(self, vector_store: VectorStore):
        self.vector_store = vector_store

    def retrieve(self, query: str, top_k: int = None, threshold: float = None) -> List[Dict[str, Any]]:
        k = top_k if top_k is not None else settings.top_k
        thresh = threshold if threshold is not None else settings.similarity_threshold
        return self.vector_store.search(query, top_k=k, threshold=thresh)
