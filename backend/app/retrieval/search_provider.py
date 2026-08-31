from typing import Protocol, List, Dict, Any
from backend.app.core.config import settings

class SearchProvider(Protocol):
    def search(self, query: str) -> List[Dict[str, Any]]: ...

class DummySearchProvider:
    def search(self, query: str) -> List[Dict[str, Any]]:
        return [
            {"title": f"Result 1 for {query}", "url": f"https://example.com/1?q={query}", "content": f"Dummy content 1 for {query}"},
            {"title": f"Result 2 for {query}", "url": f"https://example.com/2?q={query}", "content": f"Dummy content 2 for {query}"},
        ]

class DDGSearchProvider:
    def search(self, query: str) -> List[Dict[str, Any]]:
        try:
            from langchain_community.tools import DuckDuckGoSearchResults
            from langchain_community.utilities import DuckDuckGoSearchAPIWrapper
            wrapper = DuckDuckGoSearchAPIWrapper(max_results=3)
            tool = DuckDuckGoSearchResults(api_wrapper=wrapper, output_format="list")
            results = tool.invoke(query)
            formatted_results = []
            if isinstance(results, list):
                for r in results:
                    formatted_results.append({
                        "title": r.get("title", "Unknown"),
                        "url": r.get("link", ""),
                        "content": r.get("snippet", "")
                    })
            
            # Fallback to wikipedia if duckduckgo fails or returns 0 results
            if not formatted_results:
                raise Exception("DDG returned 0 results, falling back to Wikipedia")
                
            return formatted_results
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"DDG Search failed: {e}. Trying Wikipedia.")
            try:
                import wikipedia
                wikipedia.set_lang("en")
                search_results = wikipedia.search(query, results=2)
                formatted_results = []
                for title in search_results:
                    try:
                        page = wikipedia.page(title, auto_suggest=False)
                        formatted_results.append({
                            "title": page.title,
                            "url": page.url,
                            "content": page.summary[:1000]
                        })
                    except Exception:
                        pass
                return formatted_results
            except ImportError:
                logging.getLogger(__name__).warning("wikipedia package not installed.")
                return []
            except Exception as we:
                logging.getLogger(__name__).warning(f"Wikipedia search also failed: {we}")
                return []

def get_search_provider() -> SearchProvider:
    if settings.gemini_api_key not in ["your_gemini_api_key_here", "dummy"]:
        return DDGSearchProvider()
    return DummySearchProvider()
