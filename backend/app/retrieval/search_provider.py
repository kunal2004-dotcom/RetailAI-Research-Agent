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
                import httpx
                import urllib.parse
                
                # Setup custom user agent
                headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"}
                
                search_url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={urllib.parse.quote(query)}&utf8=&format=json"
                
                with httpx.Client(headers=headers, timeout=10.0) as client:
                    resp = client.get(search_url)
                    resp.raise_for_status()
                    data = resp.json()
                    search_results = [r["title"] for r in data.get("query", {}).get("search", [])][:2]
                    
                    if not search_results:
                        # Try simpler query
                        words = query.split()
                        if len(words) > 2:
                            simplified = " ".join(words[:2])
                            search_url2 = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={urllib.parse.quote(simplified)}&utf8=&format=json"
                            resp2 = client.get(search_url2)
                            data2 = resp2.json()
                            search_results = [r["title"] for r in data2.get("query", {}).get("search", [])][:2]
                            
                        if not search_results:
                            search_url3 = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch=Artificial%20Intelligence%20Retail&utf8=&format=json"
                            resp3 = client.get(search_url3)
                            data3 = resp3.json()
                            search_results = [r["title"] for r in data3.get("query", {}).get("search", [])][:2]

                    formatted_results = []
                    for title in search_results:
                        try:
                            # Get the page summary
                            summary_url = f"https://en.wikipedia.org/w/api.php?format=json&action=query&prop=extracts&exintro&explaintext&redirects=1&titles={urllib.parse.quote(title)}"
                            page_resp = client.get(summary_url)
                            page_data = page_resp.json()
                            pages = page_data.get("query", {}).get("pages", {})
                            for page_id, page_info in pages.items():
                                if page_id != "-1":
                                    formatted_results.append({
                                        "title": page_info.get("title", ""),
                                        "url": f"https://en.wikipedia.org/wiki/{urllib.parse.quote(page_info.get('title', ''))}",
                                        "content": page_info.get("extract", "")[:1000]
                                    })
                        except Exception:
                            pass
                            
                return formatted_results
            except Exception as we:
                logging.getLogger(__name__).warning(f"Wikipedia search also failed: {we}")
                return []

def get_search_provider() -> SearchProvider:
    if settings.gemini_api_key not in ["your_gemini_api_key_here", "dummy"]:
        return DDGSearchProvider()
    return DummySearchProvider()
