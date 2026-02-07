#!/usr/bin/env python3
"""
OpenAPI Query Script

Retrieves relevant API endpoint documentation from the vector store
based on natural language queries.
"""

import sys
from typing import List

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain.docstore.document import Document

import config


def load_vector_store() -> Chroma:
    """
    Load the existing ChromaDB vector store.
    
    Returns:
        ChromaDB vector store instance
        
    Raises:
        SystemExit: If vector store doesn't exist or can't be loaded
    """
    if not config.VECTOR_STORE_PATH.exists():
        print(f"Error: Vector store not found at {config.VECTOR_STORE_PATH}")
        print("Please run ingest.py first to create the vector store.")
        sys.exit(1)
    
    try:
        # Initialize embeddings model (must match the one used during ingestion)
        embeddings = HuggingFaceEmbeddings(
            model_name=config.EMBEDDING_MODEL,
            model_kwargs={'device': 'cpu'}
        )
        
        # Load the persisted vector store
        vectorstore = Chroma(
            persist_directory=str(config.VECTOR_STORE_PATH),
            embedding_function=embeddings
        )
        
        return vectorstore
        
    except Exception as e:
        print(f"Error loading vector store: {e}")
        sys.exit(1)


def query_api_docs(query: str, k: int = 5) -> List[Document]:
    """
    Query the vector store for relevant API documentation.
    
    Args:
        query: Natural language query
        k: Number of results to return (default: 5)
        
    Returns:
        List of relevant Document objects
    """
    print(f"Loading vector store from {config.VECTOR_STORE_PATH}...")
    vectorstore = load_vector_store()
    
    print(f"Searching for: '{query}'")
    print(f"Retrieving top {k} results...\n")
    
    # Perform similarity search
    results = vectorstore.similarity_search(query, k=k)
    
    return results


def format_document(doc: Document, index: int) -> str:
    """
    Format a document for display.
    
    Args:
        doc: Document object
        index: Result number (1-based)
        
    Returns:
        Formatted string representation
    """
    metadata = doc.metadata
    lines = [
        f"\n{'='*80}",
        f"Result {index}",
        f"{'='*80}",
        f"Method: {metadata.get('method', 'N/A')}",
        f"Path: {metadata.get('path', 'N/A')}",
        f"Operation ID: {metadata.get('operation_id', 'N/A')}",
        f"API: {metadata.get('api_title', 'N/A')} v{metadata.get('api_version', 'N/A')}",
        f"Tags: {', '.join(metadata.get('tags', []))}",
        f"\n{'-'*80}",
        f"Content:",
        f"{'-'*80}",
        doc.page_content,
        f"{'='*80}\n"
    ]
    
    return "\n".join(lines)


def main():
    """Main entry point for the query script."""
    if len(sys.argv) < 2:
        print("Usage: python query.py \"Your question about the API\"")
        print("\nExamples:")
        print("  python query.py \"How do I create a new device?\"")
        print("  python query.py \"What endpoints are available for user management?\"")
        print("  python query.py \"Show me authentication endpoints\"")
        sys.exit(1)
    
    # Get query from command line arguments
    query = " ".join(sys.argv[1:])
    
    # Query the vector store
    results = query_api_docs(query)
    
    if not results:
        print("No results found.")
        sys.exit(0)
    
    # Display results
    print(f"Found {len(results)} relevant API endpoints:\n")
    
    for i, doc in enumerate(results, 1):
        print(format_document(doc, i))
    
    print(f"\nContext retrieval complete. {len(results)} endpoint(s) returned.")


if __name__ == "__main__":
    main()
