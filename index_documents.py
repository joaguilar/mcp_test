import os
import glob
import uuid
import json
import datetime
import logging

from dotenv import load_dotenv
import openai
import tiktoken

# Langchain imports
from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import CharacterTextSplitter, RecursiveCharacterTextSplitter
from langchain.embeddings.openai import OpenAIEmbeddings

# OpenSearch
from opensearchpy import OpenSearch, helpers

# Load environment variables from .env file
load_dotenv()

# Configuration from .env
PDF_DIR = os.getenv("PDF_DIR", "./pdfs")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_SUMMARY_MODEL = os.getenv("OPENAI_SUMMARY_MODEL", "gpt4o-mini")
OPENAI_EMBEDDINGS_MODEL = os.getenv("OPENAI_EMBEDDINGS_MODEL", "text-embedding-ada-002")
SUMMARY_MAX_TOKENS = int(os.getenv("SUMMARY_MAX_TOKENS", "300"))  # max tokens for summary output
CONTEXT_MAX_TOKENS = int(os.getenv("CONTEXT_MAX_TOKENS", "2048"))  # max tokens allowed for summary input

# OpenSearch configuration
OPENSEARCH_HOST = os.getenv("OPENSEARCH_HOST", "localhost")
OPENSEARCH_PORT = int(os.getenv("OPENSEARCH_PORT", "9200"))
OPENSEARCH_USER = os.getenv("OPENSEARCH_USER", "")
OPENSEARCH_PASSWORD = os.getenv("OPENSEARCH_PASSWORD", "")
OPENSEARCH_INDEX = os.getenv("OPENSEARCH_INDEX", "documents")

# Chunking mode: "paragraph" or "semantic"
CHUNK_MODE = os.getenv("CHUNK_MODE", "paragraph")

# Set up OpenAI API key
openai.api_key = OPENAI_API_KEY

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def count_tokens(text: str, model: str) -> int:
    """Return number of tokens in text for the given model."""
    encoding = tiktoken.encoding_for_model(model)
    tokens = encoding.encode(text)
    return len(tokens)


def truncate_text(text: str, max_tokens: int, model: str) -> str:
    """Truncate text so that it does not exceed max_tokens."""
    encoding = tiktoken.encoding_for_model(model)
    tokens = encoding.encode(text)
    if len(tokens) <= max_tokens:
        return text
    truncated_tokens = tokens[:max_tokens]
    return encoding.decode(truncated_tokens)


def generate_summary(text: str) -> str:
    """
    Generate a summary of the given text using OpenAI completions.
    Truncates the input if needed so that it fits within the model’s context.
    """
    prompt = f"Summarize the following document:\n\n{text}\n\nSummary:"
    # Truncate prompt if too long
    prompt = truncate_text(prompt, CONTEXT_MAX_TOKENS, OPENAI_SUMMARY_MODEL)
    try:
        response = openai.Completion.create(
            model=OPENAI_SUMMARY_MODEL,
            prompt=prompt,
            max_tokens=SUMMARY_MAX_TOKENS,
            temperature=0.5,
            n=1,
            stop=None
        )
        summary = response.choices[0].text.strip()
        logger.info("Summary generated successfully.")
        return summary
    except Exception as e:
        logger.error(f"Error generating summary: {e}")
        return ""


def chunk_document(text: str) -> list:
    """
    Chunk the input text based on the selected CHUNK_MODE.
    For 'paragraph' mode the text is split on double newlines.
    For 'semantic' mode, a RecursiveCharacterTextSplitter is used.
    """
    chunks = []
    if CHUNK_MODE.lower() == "paragraph":
        # Simple paragraph split – ignore empty paragraphs
        for paragraph in text.split("\n\n"):
            p = paragraph.strip()
            if p:
                chunks.append(p)
        logger.info(f"Document split into {len(chunks)} paragraph chunks.")
    elif CHUNK_MODE.lower() == "semantic":
        # Use a more advanced splitter
        splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        chunks = splitter.split_text(text)
        logger.info(f"Document split into {len(chunks)} semantic chunks.")
    else:
        logger.warning("Unknown CHUNK_MODE specified. Defaulting to paragraph split.")
        for paragraph in text.split("\n\n"):
            p = paragraph.strip()
            if p:
                chunks.append(p)
    return chunks


def get_embedding(text: str, embedder: OpenAIEmbeddings) -> list:
    """Generate an embedding for the given text using OpenAI embeddings."""
    try:
        embedding = embedder.embed_query(text)
        return embedding
    except Exception as e:
        logger.error(f"Error generating embedding: {e}")
        return []


def create_opensearch_client() -> OpenSearch:
    """Creates and returns an OpenSearch client."""
    client = OpenSearch(
        hosts=[{'host': OPENSEARCH_HOST, 'port': OPENSEARCH_PORT}],
        http_auth=(OPENSEARCH_USER, OPENSEARCH_PASSWORD) if OPENSEARCH_USER and OPENSEARCH_PASSWORD else None,
        use_ssl=False,  # Set to True if SSL is required
        verify_certs=False
    )
    return client


def create_index_if_not_exists(client: OpenSearch, index_name: str):
    """Creates the OpenSearch index with the necessary mapping if it does not exist."""
    if client.indices.exists(index=index_name):
        logger.info(f"Index '{index_name}' already exists.")
        return

    mapping = {
        "settings": {
            "number_of_shards": 1,
            "number_of_replicas": 0
        },
        "mappings": {
            "properties": {
                "file_name": {"type": "keyword"},
                "file_path": {"type": "keyword"},
                "summary": {"type": "text"},
                "timestamp": {"type": "date"},
                "chunk_text": {"type": "text"},
                "embedding": {
                    "type": "dense_vector",
                    "dims": 1536  # for text-embedding-ada-002
                },
                "my_join_field": {
                    "type": "join",
                    "relations": {
                        "document": "chunk"
                    }
                }
            }
        }
    }
    client.indices.create(index=index_name, body=mapping)
    logger.info(f"Index '{index_name}' created with mapping.")


def index_documents_to_opensearch(client: OpenSearch, parent_doc: dict, child_docs: list):
    """Indexes the parent document and its child chunk documents."""
    actions = []

    # Prepare parent document
    parent_action = {
        "_op_type": "index",
        "_index": OPENSEARCH_INDEX,
        "_id": parent_doc["doc_id"],
        "_source": parent_doc
    }
    actions.append(parent_action)

    # Prepare child documents with join field linking to parent
    for child in child_docs:
        action = {
            "_op_type": "index",
            "_index": OPENSEARCH_INDEX,
            "_id": child["chunk_id"],
            "_source": child,
            "routing": parent_doc["doc_id"]  # ensure parent-child routing
        }
        actions.append(action)

    try:
        helpers.bulk(client, actions)
        logger.info(f"Indexed parent doc {parent_doc['doc_id']} with {len(child_docs)} child chunks.")
    except Exception as e:
        logger.error(f"Error during bulk indexing: {e}")


def process_pdf_file(file_path: str, embedder: OpenAIEmbeddings, client: OpenSearch):
    """Process a single PDF file: load, summarize, chunk, embed, and index."""
    try:
        logger.info(f"Processing file: {file_path}")
        loader = PyPDFLoader(file_path)
        documents = loader.load()  # returns a list of Langchain Document objects
        # Combine all pages into one text
        full_text = "\n\n".join([doc.page_content for doc in documents])
    except Exception as e:
        logger.error(f"Error loading PDF {file_path}: {e}")
        return

    # Generate summary for the full document
    summary = generate_summary(full_text)

    # Chunk the text
    chunks = chunk_document(full_text)

    child_docs = []
    for chunk in chunks:
        # Concatenate the summary with the chunk text for context
        context_text = f"Summary: {summary}\n\n{chunk}"
        embedding = get_embedding(context_text, embedder)
        child_doc = {
            "chunk_id": str(uuid.uuid4()),
            "chunk_text": chunk,
            "embedding": embedding,
            "my_join_field": {"name": "chunk", "parent": None}  # parent will be set in index_documents_to_opensearch
        }
        child_docs.append(child_doc)

    # Create a parent document with metadata and summary
    parent_doc_id = str(uuid.uuid4())
    parent_doc = {
        "doc_id": parent_doc_id,
        "file_name": os.path.basename(file_path),
        "file_path": os.path.abspath(file_path),
        "summary": summary,
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "my_join_field": "document"
    }

    # Set parent id in each child join field
    for child in child_docs:
        child["my_join_field"]["parent"] = parent_doc_id

    # Index documents into OpenSearch
    index_documents_to_opensearch(client, parent_doc, child_docs)


def main():
    # Create OpenSearch client and index if necessary
    client = create_opensearch_client()
    create_index_if_not_exists(client, OPENSEARCH_INDEX)

    # Initialize OpenAI embeddings embedder
    embedder = OpenAIEmbeddings(model=OPENAI_EMBEDDINGS_MODEL, openai_api_key=OPENAI_API_KEY)

    # Find all PDFs in the directory
    pdf_files = glob.glob(os.path.join(PDF_DIR, "*.pdf"))
    if not pdf_files:
        logger.warning(f"No PDF files found in directory: {PDF_DIR}")
        return

    for file_path in pdf_files:
        process_pdf_file(file_path, embedder, client)


if __name__ == "__main__":
    main()
