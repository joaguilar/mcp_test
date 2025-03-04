import os
import logging
from dotenv import load_dotenv

from opensearchpy import OpenSearch
import openai
from langchain.embeddings.openai import OpenAIEmbeddings

# Import the model context protocol sdk components.
# (Adjust the import according to your MCP SDK installation.)
from mcp import MCPServer, MCPRequest, MCPResponse

# Load configuration from .env file
load_dotenv()

# Logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# OpenSearch configuration from .env
OPENSEARCH_HOST = os.getenv("OPENSEARCH_HOST", "localhost")
OPENSEARCH_PORT = int(os.getenv("OPENSEARCH_PORT", "9200"))
OPENSEARCH_USER = os.getenv("OPENSEARCH_USER", "")
OPENSEARCH_PASSWORD = os.getenv("OPENSEARCH_PASSWORD", "")
OPENSEARCH_INDEX = os.getenv("OPENSEARCH_INDEX", "documents")

# OpenAI configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_EMBEDDINGS_MODEL = os.getenv("OPENAI_EMBEDDINGS_MODEL", "text-embedding-ada-002")
openai.api_key = OPENAI_API_KEY

# Initialize OpenAI embeddings (via Langchain)
embedder = OpenAIEmbeddings(model=OPENAI_EMBEDDINGS_MODEL, openai_api_key=OPENAI_API_KEY)

def create_opensearch_client() -> OpenSearch:
    """Creates and returns an OpenSearch client."""
    client = OpenSearch(
        hosts=[{'host': OPENSEARCH_HOST, 'port': OPENSEARCH_PORT}],
        http_auth=(OPENSEARCH_USER, OPENSEARCH_PASSWORD) if OPENSEARCH_USER and OPENSEARCH_PASSWORD else None,
        use_ssl=False,  # Change if SSL is required
        verify_certs=False
    )
    return client

# Create an OpenSearch client instance
client = create_opensearch_client()

def handle_query(request: MCPRequest) -> MCPResponse:
    """
    Process a user request by:
    1. Vectorizing the query.
    2. Executing a hybrid (join) query on OpenSearch to retrieve parent document metadata.
    3. Returning an MCP response with the results.
    """
    # 1. Retrieve and vectorize the query text from the MCPRequest
    query_text = request.query  # Assumes MCPRequest has a field "query"
    logger.info(f"Received query: {query_text}")
    
    # Vectorize the user query
    query_vector = embedder.embed_query(query_text)
    logger.info("Query vectorization complete.")

    # 2. Construct a hybrid (join) OpenSearch query.
    # This query searches for child documents (type "chunk") using a script_score that
    # computes cosine similarity between the query vector and the stored chunk embeddings.
    # The "has_child" clause ensures that matching child chunks are linked to their parent document.
    opensearch_query = {
        "query": {
            "has_child": {
                "type": "chunk",
                "query": {
                    "script_score": {
                        "query": {
                            "bool": {
                                "should": [
                                    {"match": {"chunk_text": query_text}}
                                ]
                            }
                        },
                        "script": {
                            "source": "cosineSimilarity(params.query_vector, 'embedding') + 1.0",
                            "params": {"query_vector": query_vector}
                        }
                    }
                },
                "score_mode": "max"
            }
        }
    }
    logger.info("Executing OpenSearch query...")
    try:
        search_response = client.search(index=OPENSEARCH_INDEX, body=opensearch_query)
    except Exception as e:
        logger.error(f"Error executing search: {e}")
        return MCPResponse(error=str(e))

    # 3. Process the search results – extract parent document metadata.
    hits = search_response.get("hits", {}).get("hits", [])
    logger.info(f"Found {len(hits)} matching parent documents.")
    results = []
    for hit in hits:
        source = hit["_source"]
        parent_info = {
            "doc_id": hit["_id"],
            "file_name": source.get("file_name"),
            "file_path": source.get("file_path"),
            "summary": source.get("summary"),
            "timestamp": source.get("timestamp")
        }
        results.append(parent_info)

    # 4. Construct and return an MCPResponse
    return MCPResponse(results=results)

if __name__ == "__main__":
    # Initialize and start the MCP server.
    # The server listens for incoming MCPRequests and uses handle_query to process them.
    server = MCPServer(handler=handle_query, host="0.0.0.0", port=8000)
    logger.info("Starting MCP Server on 0.0.0.0:8000")
    server.run()
