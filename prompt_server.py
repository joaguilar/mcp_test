import os
from mcp import MCPServer, Prompt, PromptRequest, PromptResponse
from dotenv import load_dotenv

load_dotenv()
# A simple "research" prompt template (not strictly used here, 
# but included to demonstrate a Prompt server).
RESEARCH_PROMPT_TEMPLATE = """
You are a research assistant. 
Given the following search results, provide a concise summary of the most relevant information.

Search Results:
{search_results}

Summary:
"""

def research_prompt(request: PromptRequest) -> PromptResponse:
    """
    A placeholder 'Prompt' implementation. 
    In a real scenario, you might pass this prompt to an LLM.
    """
    search_results = request.variables.get("search_results", [])
    mock_summary = "Trivial summary from Prompt server. (Not actively used by the main agent.)"
    return PromptResponse(
        output={"summary": mock_summary},
        debug={"info": "This prompt server is just a placeholder."}
    )

if __name__ == "__main__":
    server = MCPServer(
        name="research-prompt-server",
        prompts=[Prompt(name="researchPrompt", handler=research_prompt)]
    )
    server.run(host="0.0.0.0", port=5002)
