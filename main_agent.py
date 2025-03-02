import streamlit as st
import os
from mcp import MCPClient

# MCP server endpoints (adjust if using different ports)
TOOLS_SERVER_URL = "http://localhost:5001"       # Brave search tools
PROMPT_SERVER_URL = "http://localhost:5002"      # Prompt server (placeholder)
DB_RESOURCE_SERVER_URL = "http://localhost:5003" # DB resource (SQLite) server
LLM_SERVER_URL = "http://localhost:5004"         # Sampler server (OpenAI GPT)

def run_research_query(query: str):
    """
    Main orchestration:
      1. Search the web for the query using Tools server (Brave).
      2. Search the local DB (papers.db) for matching references.
      3. Call the LLM Sampler to synthesize a final, retrieval-augmented answer.
      4. Return final text to display in UI.
    """
    # -------------------------
    # (1) Web Search (Tools)
    # -------------------------
    tools_client = MCPClient(TOOLS_SERVER_URL)
    search_response = tools_client.tools.call(
        tool_name="searchWeb", 
        tool_input={"query": query, "limit": 3}
    )
    web_results = search_response.get("results", [])

    # -------------------------
    # (2) Local DB Search
    # -------------------------
    db_client = MCPClient(DB_RESOURCE_SERVER_URL)
    db_response = db_client.resources.call(
        resource_name="searchPapers",
        resource_input={"query": query}
    )
    db_matches = db_response.get("results", [])
    
    # Format DB matches for the LLM context
    # E.g., "Paper Title: ... Abstract: ... Authors: ..."
    db_text_snippets = []
    for paper in db_matches:
        snippet = (
            f"Title: {paper['title']}\n"
            f"Authors: {paper['authors']}\n"
            f"Abstract: {paper['abstract']}"
        )
        db_text_snippets.append(snippet)

    # -------------------------
    # Combine all context
    # -------------------------
    combined_search_context = "=== Web Results ===\n"
    combined_search_context += "\n\n".join(web_results) if web_results else "No web results.\n"
    combined_search_context += "\n\n=== DB Papers ===\n"
    combined_search_context += "\n\n".join(db_text_snippets) if db_text_snippets else "No local DB matches.\n"

    # -------------------------
    # (3) LLM Sampler Summarization
    # -------------------------
    sampler_client = MCPClient(LLM_SERVER_URL)
    # We'll pass a "system" message and a "user" message with all context
    system_msg = (
        "You are a helpful research assistant. "
        "Combine the following web search results and database papers to answer the user's query."
    )
    user_msg = f"User query: {query}\n\nSearch context:\n{combined_search_context}\n"

    sample_response = sampler_client.samplings.sample(
        sampler_name="openai-chat",
        prompt={
            "system": system_msg,
            "user": user_msg
        },
        settings={"temperature": 0.4}
    )
    final_answer = sample_response.get("text", "[No answer returned from LLM]")

    return final_answer

# Streamlit UI
def main():
    st.title("MCP Research Agent (with DB Resource) Demo")
    
    user_query = st.text_input("Enter your research query:")
    
    if st.button("Run Research"):
        if not user_query.strip():
            st.warning("Please enter a query.")
        else:
            with st.spinner("Searching & Synthesizing..."):
                result = run_research_query(user_query.strip())
                st.success("Completed!")
                st.write("**Answer:**")
                st.write(result)

if __name__ == "__main__":
    main()
