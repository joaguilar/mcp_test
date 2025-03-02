import os
import sqlite3
from typing import List
from mcp import MCPServer, Resource, ResourceRequest, ResourceResponse

DATABASE_FILE = "papers.db"

def init_db():
    """
    Create and populate a 'papers' table with some famous LLM & IR papers.
    If the table already exists, it won't overwrite data.
    """
    conn = sqlite3.connect(DATABASE_FILE)
    c = conn.cursor()

    # Create table if not exists
    c.execute("""
        CREATE TABLE IF NOT EXISTS papers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            abstract TEXT,
            authors TEXT
        )
    """)

    # Insert some well-known papers if table is empty
    c.execute("SELECT COUNT(*) FROM papers")
    count = c.fetchone()[0]
    if count == 0:
        papers_data = [
            (
                "Attention Is All You Need",
                "Introduced the Transformer architecture which became foundational to modern NLP and large language models.",
                "Vaswani et al."
            ),
            (
                "BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding",
                "Demonstrates the effectiveness of bidirectional Transformer language models on a wide variety of NLP tasks.",
                "Devlin et al."
            ),
            (
                "Language Models are Few-Shot Learners (GPT-3)",
                "Shows that scaling language model size leads to surprising few-shot learning capabilities.",
                "Brown et al."
            ),
            (
                "Okapi BM25",
                "A ranking function used by search engines to estimate the relevance of documents to a given query.",
                "Robertson et al."
            ),
            (
                "A Neural Probabilistic Language Model",
                "One of the earliest works on using neural networks for language modeling.",
                "Bengio et al."
            )
        ]
        c.executemany("INSERT INTO papers (title, abstract, authors) VALUES (?, ?, ?)", papers_data)
        conn.commit()

    conn.close()

def search_papers(query: str) -> List[dict]:
    """
    Simple search in the 'papers' table by matching 'query' against title or abstract or authors.
    Returns a list of dicts with matching papers.
    """
    conn = sqlite3.connect(DATABASE_FILE)
    c = conn.cursor()
    # Naive LIKE-based search (for demo). You could use FTS for more advanced search.
    wildcard_query = f"%{query}%"
    c.execute("""
        SELECT title, abstract, authors
        FROM papers
        WHERE title LIKE ? OR abstract LIKE ? OR authors LIKE ?
    """, (wildcard_query, wildcard_query, wildcard_query))
    rows = c.fetchall()
    conn.close()

    results = []
    for row in rows:
        results.append({
            "title": row[0],
            "abstract": row[1],
            "authors": row[2]
        })
    return results

# --- MCP Resource Handlers ---

def resource_search_papers(request: ResourceRequest) -> ResourceResponse:
    """
    Resource method that searches the 'papers' table for a matching query (keyword).
    """
    query = request.resource_input.get("query", "")
    if not query.strip():
        return ResourceResponse(
            output={"error": "No query provided."}
        )
    found = search_papers(query.strip())
    return ResourceResponse(
        output={
            "results": found,
            "count": len(found),
        }
    )

if __name__ == "__main__":
    # Initialize DB and populate if empty
    init_db()

    # Create an MCP Resource server exposing a 'searchPapers' Resource
    server = MCPServer(
        name="db-resource-server",
        resources=[
            Resource(
                name="searchPapers",
                handler=resource_search_papers,
                description="Search for papers in a local SQLite DB by keyword in title/abstract/authors."
            ),
        ]
    )
    # Run on port 5003 (adjust as desired)
    server.run(host="0.0.0.0", port=5028)
