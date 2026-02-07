"""
FastAPI MCP server for OpenAPI RAG context retrieval.

This server exposes the vector store query functionality via a REST API,
allowing IDE AI assistants to retrieve relevant OpenAPI documentation context.
"""

import sys
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

# Local imports
from config import (
    VECTOR_STORE_PATH,
    EMBEDDING_MODEL,
    MCP_HOST,
    MCP_PORT
)

# Configure logging
LOG_FILE = Path(__file__).parent / "server.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Global vector store instance
vector_store = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    global vector_store
    
    # Startup
    try:
        logger.info("Loading vector store...")
        vector_store = load_vector_store()
        logger.info(f"✓ Vector store loaded from {VECTOR_STORE_PATH}")
        logger.info(f"✓ Server ready at http://{MCP_HOST}:{MCP_PORT}")
    except Exception as e:
        logger.error(f"✗ Failed to initialize server: {e}", exc_info=True)
        sys.exit(1)
    
    yield
    
    # Shutdown (cleanup if needed)
    logger.info("Shutting down server...")
    vector_store = None


# Initialize FastAPI app with lifespan
app = FastAPI(
    title="OpenAPI MCP Server",
    description="Retrieval-Augmented Generation server for OpenAPI specifications",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS for IDE integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for local development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class QueryRequest(BaseModel):
    """Request model for /query endpoint."""
    query: str = Field(..., description="Natural language query about the API", min_length=1)
    k: Optional[int] = Field(3, description="Number of results to return", ge=1, le=20)


class DocumentResult(BaseModel):
    """Model for a single document result."""
    content: str = Field(..., description="The document content")
    metadata: Dict[str, Any] = Field(..., description="Document metadata")
    relevance_score: Optional[float] = Field(None, description="Similarity score (if available)")


class QueryResponse(BaseModel):
    """Response model for /query endpoint."""
    query: str = Field(..., description="The original query")
    results: List[DocumentResult] = Field(..., description="List of relevant documents")
    count: int = Field(..., description="Number of results returned")


def load_vector_store() -> Chroma:
    """
    Load the ChromaDB vector store from disk.
    
    Returns:
        Chroma: The loaded vector store instance
        
    Raises:
        FileNotFoundError: If vector store doesn't exist
        RuntimeError: If loading fails
    """
    if not VECTOR_STORE_PATH.exists():
        raise FileNotFoundError(
            f"Vector store not found at {VECTOR_STORE_PATH}. "
            "Please run ingest.py first to create the vector store."
        )
    
    try:
        # Initialize embeddings model
        embeddings = HuggingFaceEmbeddings(
            model_name=EMBEDDING_MODEL,
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )
        
        # Load the persisted vector store
        vector_store = Chroma(
            persist_directory=str(VECTOR_STORE_PATH),
            embedding_function=embeddings
        )
        
        return vector_store
    except Exception as e:
        raise RuntimeError(f"Failed to load vector store: {e}")


def format_document(doc: Any, score: Optional[float] = None) -> DocumentResult:
    """
    Format a LangChain Document into a structured result.
    
    Args:
        doc: LangChain Document object
        score: Optional relevance score
        
    Returns:
        DocumentResult: Formatted document result
    """
    return DocumentResult(
        content=doc.page_content,
        metadata=doc.metadata,
        relevance_score=score
    )


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "vector_store_loaded": vector_store is not None,
        "vector_store_path": str(VECTOR_STORE_PATH)
    }


@app.post("/query", response_model=QueryResponse)
async def query_endpoint(request: QueryRequest):
    """
    Query the OpenAPI documentation using natural language.
    
    Args:
        request: QueryRequest with query string and optional k parameter
        
    Returns:
        QueryResponse: List of relevant documents with metadata
        
    Raises:
        HTTPException: If vector store not initialized or query fails
    """
    if vector_store is None:
        raise HTTPException(
            status_code=503,
            detail="Vector store not initialized. Please check server logs."
        )
    
    try:
        # Perform similarity search with scores
        results_with_scores = vector_store.similarity_search_with_score(
            request.query,
            k=request.k
        )
        
        # Format results
        formatted_results = [
            format_document(doc, score)
            for doc, score in results_with_scores
        ]
        
        return QueryResponse(
            query=request.query,
            results=formatted_results,
            count=len(formatted_results)
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Query failed: {str(e)}"
        )


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "OpenAPI MCP Server",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "query": "/query (POST)",
            "docs": "/docs"
        }
    }


def main():
    """Run the FastAPI server."""
    uvicorn.run(
        "server:app",
        host=MCP_HOST,
        port=MCP_PORT,
        reload=True,
        log_level="info"
    )


if __name__ == "__main__":
    main()
