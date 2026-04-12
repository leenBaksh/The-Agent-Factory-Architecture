"""
Web Search MCP Server for Digital FTEs

Provides tool access for:
- Web searching
- Real-time information retrieval
- Fact checking
- Research and competitive analysis
"""

import os
import logging
from typing import Optional

import httpx
from mcp.server.fastmcp import FastMCP

logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP(
    "web-search-server",
    description="Web search integration for research and fact-checking",
    dependencies=["httpx"],
)

# Search engine configuration
SEARCH_API_KEY = os.getenv("SEARCH_API_KEY")  # SerpAPI, Google Custom Search, etc.
SEARCH_ENGINE_ID = os.getenv("SEARCH_ENGINE_ID")


@mcp.tool()
async def web_search(
    query: str,
    num_results: int = 10,
    language: str = "en",
    country: Optional[str] = None,
) -> dict:
    """
    Perform a web search and return results.

    Args:
        query: Search query
        num_results: Number of results (default: 10, max: 20)
        language: Language code (default: en)
        country: Optional country code for localization

    Returns:
        dict with search results including title, URL, snippet
    """
    num_results = min(num_results, 20)

    # Using Google Custom Search API as example
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": SEARCH_API_KEY,
        "cx": SEARCH_ENGINE_ID,
        "q": query,
        "num": num_results,
        "lr": f"lang_{language}",
    }
    
    if country:
        params["cr"] = f"country{country}"
        params["gl"] = country

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, params=params, timeout=10.0)
            response.raise_for_status()
            data = response.json()

            if "items" not in data:
                return {"success": False, "error": "No results found", "results": []}

            results = [
                {
                    "title": item.get("title", ""),
                    "url": item.get("link", ""),
                    "snippet": item.get("snippet", ""),
                    "display_link": item.get("displayLink", ""),
                }
                for item in data["items"][:num_results]
            ]

            return {
                "success": True,
                "query": query,
                "results": results,
                "count": len(results),
            }
        except httpx.HTTPError as e:
            logger.error(f"Web search failed: {e}")
            return {"success": False, "error": str(e), "results": []}


@mcp.tool()
async def search_news(
    query: str,
    num_results: int = 10,
    days: int = 7,
) -> dict:
    """
    Search for recent news articles.

    Args:
        query: News search query
        num_results: Number of results (default: 10)
        days: How many days back to search (default: 7)

    Returns:
        dict with news articles including title, URL, source, date
    """
    num_results = min(num_results, 20)

    # Using News API as example
    url = "https://newsapi.org/v2/everything"
    params = {
        "apiKey": os.getenv("NEWS_API_KEY"),
        "q": query,
        "pageSize": num_results,
        "sortBy": "relevancy",
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, params=params, timeout=10.0)
            response.raise_for_status()
            data = response.json()

            if data.get("status") != "ok":
                return {"success": False, "error": data.get("message", "Unknown error"), "results": []}

            results = [
                {
                    "title": article.get("title", ""),
                    "url": article.get("url", ""),
                    "source": article.get("source", {}).get("name", ""),
                    "published_at": article.get("publishedAt", ""),
                    "description": article.get("description", ""),
                }
                for article in data.get("articles", [])[:num_results]
            ]

            return {
                "success": True,
                "query": query,
                "results": results,
                "count": len(results),
            }
        except httpx.HTTPError as e:
            logger.error(f"News search failed: {e}")
            return {"success": False, "error": str(e), "results": []}


@mcp.tool()
async def fetch_url_content(
    url: str,
    max_length: int = 5000,
) -> dict:
    """
    Fetch and extract content from a URL.

    Args:
        url: URL to fetch
        max_length: Maximum characters to return (default: 5000)

    Returns:
        dict with title and content excerpt
    """
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                url,
                timeout=10.0,
                follow_redirects=True,
                headers={
                    "User-Agent": "Mozilla/5.0 (Digital FTE Web Search MCP)"
                },
            )
            response.raise_for_status()

            # Extract title
            title = ""
            if "<title>" in response.text:
                start = response.text.index("<title>") + 7
                end = response.text.index("</title>")
                title = response.text[start:end].strip()

            # Extract basic content (simplified - in production use BeautifulSoup)
            content = response.text[:max_length]

            return {
                "success": True,
                "url": url,
                "title": title,
                "content_excerpt": content,
                "status_code": response.status_code,
            }
        except httpx.HTTPError as e:
            logger.error(f"URL fetch failed: {e}")
            return {"success": False, "error": str(e)}


@mcp.tool()
async def search_wikipedia(
    query: str,
    num_results: int = 5,
) -> dict:
    """
    Search Wikipedia for information.

    Args:
        query: Search query
        num_results: Number of results (default: 5)

    Returns:
        dict with Wikipedia article summaries
    """
    num_results = min(num_results, 10)

    # Search
    search_url = "https://en.wikipedia.org/w/api.php"
    search_params = {
        "action": "query",
        "list": "search",
        "srsearch": query,
        "srlimit": num_results,
        "format": "json",
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(search_url, params=search_params, timeout=10.0)
            response.raise_for_status()
            data = response.json()

            results = []
            for item in data.get("query", {}).get("search", [])[:num_results]:
                # Get summary
                summary_params = {
                    "action": "query",
                    "prop": "extracts",
                    "exintro": True,
                    "explaintext": True,
                    "pageids": item["pageid"],
                    "format": "json",
                }
                summary_resp = await client.get(search_url, params=summary_params, timeout=10.0)
                summary_data = summary_resp.json()
                pages = summary_data.get("query", {}).get("pages", {})
                summary = list(pages.values())[0].get("extract", "") if pages else ""

                results.append({
                    "title": item["title"],
                    "url": f"https://en.wikipedia.org/wiki/{item['title'].replace(' ', '_')}",
                    "summary": summary[:500],
                    "word_count": item.get("wordcount", 0),
                })

            return {
                "success": True,
                "query": query,
                "results": results,
                "count": len(results),
            }
        except httpx.HTTPError as e:
            logger.error(f"Wikipedia search failed: {e}")
            return {"success": False, "error": str(e), "results": []}


if __name__ == "__main__":
    mcp.run()
