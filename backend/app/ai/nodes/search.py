import logging
from datetime import datetime, timezone
from backend.app.ai.state import ResearchState
from backend.app.retrieval.search_provider import get_search_provider

logger = logging.getLogger(__name__)

def search_sources(state: ResearchState) -> ResearchState:
    logger.info(f"Session {state['session_id']}: Running Search")
    state["current_step"] = "search"
    provider = get_search_provider()
    logger.info(f"Search provider: {provider.__class__.__name__}")
    seen_urls = set()
    sources = []

    try:
        for query in state["search_queries"]:
            import time
            logger.info(f"Searching for: {query}")
            results = provider.search(query)
            time.sleep(2) # Prevent DuckDuckGo rate limiting
            for r in results:
                url = r.get("url", "")
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    sources.append({
                        "temp_id": f"src_{len(sources)}",
                        "title": r.get("title", "Untitled"),
                        "url": url,
                        "source_type": "web",
                        "publisher": r.get("publisher", "Unknown"),
                        "content": r.get("content", ""),
                        "retrieved_at": datetime.now(timezone.utc).isoformat(),
                        "query": query
                    })
        state["sources"] = sources
        logger.info(f"Session {state['session_id']}: Found {len(sources)} unique sources.")
        if not sources:
            state["errors"].append("Insufficient evidence: No sources found.")
    except Exception as e:
        logger.error(f"Search error: {e}")
        state["errors"].append(f"Search error: {str(e)}")
    return state
