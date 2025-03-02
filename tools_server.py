import os
import requests
from mcp import MCPServer, Tool, ToolRequest, ToolResponse
from dotenv import load_dotenv

load_dotenv()

BRAVE_API_KEY = os.environ.get("BRAVE_API_KEY", "")
BRAVE_SEARCH_URL = "https://api.search.brave.com/res/v1/web/search"

def search_brave(query: str, limit: int = 3):
    """
    Calls Brave Search API with the provided query.
    Returns a list of search result snippets/links.
    """
    if not BRAVE_API_KEY:
        return ["[ERROR] Missing Brave API Key."]

    params = {
        "q": query,
        "count": limit,
        "offset": 0,
        "source": "web"
    }
    headers = {"X-Subscription-Token": BRAVE_API_KEY}

    try:
        response = requests.get(BRAVE_SEARCH_URL, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        results = []
        for entry in data.get("web", []):
            title = entry.get("title", "No Title")
            link = entry.get("url", "No URL")
            snippet = entry.get("description", "No Description")
            results.append(f"Title: {title}\nURL: {link}\nSnippet: {snippet}")
        return results
    except Exception as e:
        return [f"[ERROR] Brave API request failed: {e}"]

def brave_search_tool(request: ToolRequest) -> ToolResponse:
    """
    MCP Tool handler for searching the web using Brave.
    """
    query = request.tool_input.get("query", "")
    limit = request.tool_input.get("limit", 3)
    results = search_brave(query, limit=limit)
    return ToolResponse(output={"results": results})

if __name__ == "__main__":
    server = MCPServer(
        name="brave-tools",
        tools=[
            Tool(
                name="searchWeb",
                description="Tool to search the web via Brave Search",
                run=brave_search_tool
            )
        ]
    )
    server.run(host="0.0.0.0", port=5001)
