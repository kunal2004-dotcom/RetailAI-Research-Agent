import logging
from backend.app.ai.state import ResearchState
from backend.app.retrieval.embeddings import get_embedding_provider
from backend.app.retrieval.chroma_client import ChromaVectorStore
from backend.app.retrieval.ingestion import DocumentIngestionPipeline, Retriever

logger = logging.getLogger(__name__)

def ingest_and_retrieve(state: ResearchState) -> ResearchState:
    logger.info(f"Session {state['session_id']}: Running Ingestion & Retrieval")
    state["current_step"] = "retrieval"
    
    if any("Insufficient evidence" in err for err in state.get("errors", [])):
        return state

    try:
        embedding_provider = get_embedding_provider()
        vstore = ChromaVectorStore(embedding_provider=embedding_provider)
        
        logger.info(f"Embedding provider: {embedding_provider.__class__.__name__}")
        logger.info(f"Vector store: {vstore.__class__.__name__}")

        pipeline = DocumentIngestionPipeline(vstore)
        pipeline.ingest_sources(state.get("sources", []), state["session_id"])
        
        retriever = Retriever(vstore)
        
        retrieved_chunks = []
        seen_chunk_ids = set()
        
        for query in state.get("search_queries", []):
            results = retriever.retrieve(query)
            for r in results:
                if r["id"] not in seen_chunk_ids:
                    seen_chunk_ids.add(r["id"])
                    retrieved_chunks.append(r)
        
        state["retrieved_chunks"] = retrieved_chunks
        logger.info(f"Session {state['session_id']}: Retrieved {len(retrieved_chunks)} relevant chunks.")
        
        if not retrieved_chunks:
            state["errors"].append("Insufficient evidence: No relevant information found in retrieved chunks.")
            
    except Exception as e:
        logger.error(f"Retrieval error: {e}")
        state["errors"].append(f"Retrieval error: {str(e)}")
        
    return state
