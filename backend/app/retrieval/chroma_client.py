import chromadb
from typing import List, Dict, Any
from backend.app.core.config import settings
from backend.app.retrieval.interfaces import VectorStore, EmbeddingProvider

class ChromaVectorStore(VectorStore):
    def __init__(self, embedding_provider: EmbeddingProvider, persist_dir: str = None, client=None):
        self.embedding_provider = embedding_provider
        if client:
            self.client = client
        elif getattr(settings, "use_ephemeral_chroma", False):
            self.client = chromadb.EphemeralClient()
        else:
            self.client = chromadb.PersistentClient(path=persist_dir or settings.chroma_persist_directory)
            
        self.collection = self.client.get_or_create_collection(
            name=settings.chroma_collection_name
        )

    def add_documents(self, documents: List[Dict[str, Any]]):
        if not documents:
            return
        
        ids = [doc["id"] for doc in documents]
        texts = [doc["content"] for doc in documents]
        metadatas = [doc["metadata"] for doc in documents]
        
        embeddings = self.embedding_provider.embed_documents(texts)
        
        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas
        )

    def search(self, query: str, top_k: int = 5, threshold: float = 0.0) -> List[Dict[str, Any]]:
        query_embedding = self.embedding_provider.embed_query(query)
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["documents", "metadatas", "distances"]
        )
        
        parsed_results = []
        if not results["ids"] or not results["ids"][0]:
            return parsed_results
            
        for i in range(len(results["ids"][0])):
            distance = results["distances"][0][i]
            # Simple conversion metric for filtering
            similarity = 1.0 / (1.0 + distance) 
            
            if similarity >= threshold:
                parsed_results.append({
                    "id": results["ids"][0][i],
                    "content": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "similarity": similarity
                })
                
        return parsed_results
