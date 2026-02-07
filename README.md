# OpenAPI MCP - Local RAG System for OpenAPI Specifications

A fully local Retrieval-Augmented Generation (RAG) system that makes OpenAPI specifications searchable using natural language. This system ingests OpenAPI JSON files, creates vector embeddings, and exposes them via an MCP (Model Context Protocol) server for seamless IDE integration.

## Features

- 🔍 **Natural Language Search**: Query your API documentation using plain English
- 🏠 **Fully Local**: No external API dependencies - runs entirely on your machine
- 🚀 **Fast Vector Search**: Uses ChromaDB for efficient similarity search
- 🔌 **MCP Server**: FastAPI-based server for IDE AI assistant integration
- 📝 **Smart Chunking**: Automatically splits OpenAPI specs by endpoint for better context
- 🎯 **Semantic Embeddings**: Uses sentence-transformers for high-quality embeddings

## Architecture

```
┌─────────────────┐
│  OpenAPI JSON   │
│  Specifications │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   ingest.py     │  Processes OpenAPI specs
│                 │  Creates embeddings
└────────┬────────┘  Stores in ChromaDB
         │
         ▼
┌─────────────────┐
│   Vector Store  │  Local ChromaDB
│   (ChromaDB)    │  Persistent storage
└────────┬────────┘
         │
         ├──────────────┬─────────────┐
         ▼              ▼             ▼
┌─────────────┐  ┌──────────┐  ┌──────────┐
│  query.py   │  │server.py │  │   IDE    │
│     CLI     │  │   MCP    │  │  Plugin  │
│             │  │  Server  │  │          │
└─────────────┘  └──────────┘  └──────────┘
```

## Prerequisites

- Python 3.10 or higher
- pip (Python package manager)
- 2GB+ RAM (for embedding models)
- Git (for version control)

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/Digital-Technology-Group-LLC/open-api-mcp.git
cd open-api-mcp
```

### 2. Set Up Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate  # On macOS/Linux
# OR
venv\Scripts\activate     # On Windows
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment (Optional)

Create a `.env` file to customize settings:

```bash
cp .env.example .env
```

Edit `.env` to override defaults:

```env
# Vector store location
VECTOR_STORE_PATH=./vector_store

# Embedding model (default: all-MiniLM-L6-v2)
EMBEDDING_MODEL=all-MiniLM-L6-v2

# API specs directory
API_SPECS_DIR=./api_specs

# MCP Server settings
MCP_HOST=127.0.0.1
MCP_PORT=8888
```

### 5. Add OpenAPI Specifications

Place your OpenAPI JSON files in the `api_specs/` directory:

```bash
cp your-api-spec.json api_specs/
```

### 6. Ingest API Specifications

Process your OpenAPI specs and create embeddings:

```bash
python ingest.py
```

This will:
- Read all JSON files from `api_specs/`
- Extract each API endpoint
- Create semantic embeddings
- Store in ChromaDB vector store

### 7. Test with CLI

Query your API documentation:

```bash
python query.py "How do I authenticate?"
python query.py "What endpoints are available for user management?"
python query.py "Show me pagination parameters"
```

### 8. Start MCP Server

#### Option A: Run Locally

Launch the FastAPI server for IDE integration:

```bash
python server.py
```

Server will be available at `http://127.0.0.1:8888`

Check the logs in `server.log` for debugging.

#### Option B: Run with Docker (Recommended)

Using Docker provides easier server lifecycle management without background processes.

**Build and start the server:**
```bash
docker-compose up -d
```

**View logs:**
```bash
docker-compose logs -f
```

**Stop the server:**
```bash
docker-compose down
```

**Restart the server:**
```bash
docker-compose restart
```

**Check server status:**
```bash
docker-compose ps
curl http://localhost:8888/health
```

The Docker setup automatically:
- Mounts `vector_store/` and `api_specs/` for persistence
- Exposes the server on port 8888
- Includes health checks
- Restarts on failure
- Logs to `server.log`

**To run ingestion in the container:**
```bash
docker-compose exec openapi-mcp-server python ingest.py
```

## Usage

### Command-Line Interface (query.py)

```bash
# Basic query
python query.py "your question here"

# Query with more results
python query.py "your question" --k 5

# Examples
python query.py "How to create a user?"
python query.py "What are the rate limits?"
python query.py "Show authentication methods"
```

**Output Format:**
```
Query: "How do I authenticate?"
Found 3 relevant results:

=== Result 1 ===
Endpoint: POST /auth/login
Description: Authenticate user and receive access token
Parameters:
  - username (string, required): User's email or username
  - password (string, required): User's password
Response: Returns JWT token for subsequent requests
---
Relevance Score: 0.85

[Additional results...]
```

### MCP Server API (server.py)

#### Endpoints

**Health Check**
```bash
GET /health
```

Response:
```json
{
  "status": "healthy",
  "vector_store_loaded": true,
  "vector_store_path": "vector_store"
}
```

**Root Information**
```bash
GET /
```

Response:
```json
{
  "name": "OpenAPI MCP Server",
  "version": "1.0.0",
  "endpoints": {
    "health": "/health",
    "query": "/query (POST)",
    "docs": "/docs"
  }
}
```

**Query API Documentation**
```bash
POST /query
Content-Type: application/json

{
  "query": "How do I authenticate?",
  "k": 3
}
```

Response:
```json
{
  "query": "How do I authenticate?",
  "results": [
    {
      "content": "POST /auth/login - Authenticate user...",
      "metadata": {
        "endpoint": "POST /auth/login",
        "path": "/auth/login",
        "method": "POST"
      },
      "relevance_score": 0.85
    }
  ],
  "count": 3
}
```

#### Using cURL

```bash
# Health check
curl http://localhost:8888/health

# Query
curl -X POST http://localhost:8888/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How to create a user?",
    "k": 3
  }'
```

#### Using Python Requests

```python
import requests

# Query the API
response = requests.post(
    "http://localhost:8888/query",
    json={
        "query": "How do I authenticate?",
        "k": 5
    }
)

results = response.json()
for result in results["results"]:
    print(f"Endpoint: {result['metadata']['endpoint']}")
    print(f"Content: {result['content'][:200]}...")
    print(f"Score: {result['relevance_score']}\n")
```

### Data Ingestion (ingest.py)

The ingestion script processes OpenAPI specifications intelligently:

**What it does:**
1. Reads all `.json` files from `api_specs/`
2. Extracts each API endpoint (path + method)
3. Creates a rich document for each endpoint containing:
   - Summary and description
   - Parameters (query, path, header)
   - Request body schema
   - Response schemas
   - Tags and operation ID
4. Generates semantic embeddings using sentence-transformers
5. Stores in persistent ChromaDB vector database

**Running ingestion:**
```bash
# Process all API specs
python ingest.py

# Output
Processing: api_specs/my-api.json
  Found 15 endpoints
  Creating embeddings...
  ✓ Stored 15 documents in vector store

Total documents ingested: 15
Vector store location: vector_store
```

**Re-running ingestion:**
The script will clear and rebuild the vector store each time. If you want to preserve existing data, modify `ingest.py` to not call `collection.delete()`.

## Configuration

All configuration is managed through environment variables or `config.py`:

| Variable | Default | Description |
|----------|---------|-------------|
| `VECTOR_STORE_PATH` | `./vector_store` | Directory for ChromaDB storage |
| `EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | HuggingFace model for embeddings |
| `API_SPECS_DIR` | `./api_specs` | Directory containing OpenAPI JSON files |
| `MCP_HOST` | `127.0.0.1` | MCP server host |
| `MCP_PORT` | `8888` | MCP server port |

### Embedding Models

You can use any sentence-transformers model from HuggingFace. Popular options:

- `all-MiniLM-L6-v2` (default) - Fast, good quality, 80MB
- `all-mpnet-base-v2` - Higher quality, slower, 420MB
- `multi-qa-mpnet-base-dot-v1` - Optimized for Q&A

Change in `.env`:
```env
EMBEDDING_MODEL=all-mpnet-base-v2
```

## IDE Integration

The MCP server exposes a REST API that can be integrated with AI coding assistants. Here are the integration options:

### Option 1: Direct API Integration

Use the REST API directly in your custom tools or scripts:

**Endpoint:** `http://localhost:8888/query`  
**Method:** `POST`  
**Body:**
```json
{
  "query": "How do I authenticate?",
  "k": 3
}
```

**Response:**
```json
{
  "query": "How do I authenticate?",
  "results": [...],
  "count": 3
}
```

### Option 2: MCP Client Integration

This server implements the Model Context Protocol (MCP). To use it with MCP-compatible clients:

1. The server runs at `http://localhost:8888`
2. Use the `/query` endpoint for context retrieval
3. Query results include relevant API documentation with metadata

### Option 3: Custom IDE Extension

Build a custom extension for your IDE that:
1. Calls the `/query` endpoint with the user's question
2. Parses the returned `results` array
3. Injects the context into your AI assistant's prompt

**Example Python integration:**
```python
import requests

def get_api_context(question: str, num_results: int = 3) -> list:
    """Retrieve relevant API documentation for a question."""
    response = requests.post(
        "http://localhost:8888/query",
        json={"query": question, "k": num_results}
    )
    return response.json()["results"]

# Usage
context = get_api_context("How to create a user?")
for result in context:
    print(f"Endpoint: {result['metadata']['endpoint']}")
    print(f"Content: {result['content']}\n")
```

### Integration with GitHub Copilot / Cursor

**Note:** As of now, GitHub Copilot and Cursor don't have built-in support for external MCP servers through configuration files. 

To use this with Copilot or Cursor, you would need to:
1. Copy relevant context from query results manually
2. Use the API in a separate tool to fetch context
3. Create a custom extension that integrates with the editor

**Future Integration:** Watch for updates to GitHub Copilot's extensibility features that may support external context providers.

### Testing the API

```bash
# Test query
curl -X POST http://localhost:8888/query \
  -H "Content-Type: application/json" \
  -d '{"query": "authentication endpoints", "k": 3}'

# Check health
curl http://localhost:8888/health
```

## Development

### Project Structure

```
open-api-mcp/
├── .beads/              # Beads issue tracker
├── api_specs/           # OpenAPI JSON files (add yours here)
├── vector_store/        # ChromaDB persistent storage (auto-created)
├── venv/                # Python virtual environment
├── .env                 # Environment configuration (optional)
├── .env.example         # Example environment file
├── .gitignore           # Git ignore rules
├── config.py            # Configuration management
├── ingest.py            # OpenAPI ingestion script
├── query.py             # CLI query tool
├── server.py            # FastAPI MCP server
├── requirements.txt     # Python dependencies
├── server.log           # Server logs (auto-created)
└── README.md            # This file
```

### Running Tests

```bash
# Activate virtual environment
source venv/bin/activate

# Run ingestion
python ingest.py

# Test CLI query
python query.py "test query"

# Test server
python server.py &
curl http://localhost:8888/health
```

### Debugging

**Enable verbose logging:**

Edit `server.py` to change log level:
```python
logging.basicConfig(
    level=logging.DEBUG,  # Change from INFO to DEBUG
    # ...
)
```

**Check server logs:**
```bash
tail -f server.log
```

**Verify vector store:**
```bash
# Check if embeddings were created
ls -lh vector_store/
```

## Troubleshooting

### "No module named 'sentence_transformers'"

```bash
pip install sentence-transformers
```

### "Failed to load vector store"

Run ingestion first:
```bash
python ingest.py
```

### "Address already in use" (port 8888)

Change port in `.env`:
```env
MCP_PORT=8889
```

Or kill existing process:
```bash
lsof -ti:8888 | xargs kill -9
```

### Empty Query Results

Ensure your OpenAPI specs are valid JSON and in `api_specs/`:
```bash
ls -lh api_specs/
python -m json.tool api_specs/your-api.json
```

### Slow Embedding Generation

First run downloads the model (~80MB). Subsequent runs use cached model. For faster embedding, use a smaller model:
```env
EMBEDDING_MODEL=all-MiniLM-L6-v2
```

## Performance

- **Ingestion**: ~1-2 seconds per endpoint
- **Query**: <100ms for similarity search
- **Embedding Model**: Downloads once, cached locally
- **Memory**: ~500MB for model + embeddings

**Optimization Tips:**
- Use SSD for vector store storage
- Increase `k` parameter only when needed
- Consider GPU support for faster embeddings (requires PyTorch CUDA)

## Contributing

This project uses **Beads** for issue tracking. See [AGENTS.md](AGENTS.md) for AI agent workflows.

### Development Workflow

1. Find available work: `bd ready`
2. Create feature branch: `git checkout -b feature/open-api-mcp-<id>-<desc>`
3. Claim task: `bd update <id> --status in_progress`
4. Implement changes
5. Close issue: `bd close <id> --reason "..."`
6. Sync beads: `bd sync`
7. Commit: `git add -A && git commit -m "feat(...): ..."`
8. Push: `git push -u origin <branch>`
9. Open PR for review

## License

MIT License - See LICENSE file for details

## Support

- **Issues**: Use `bd create` for bug reports and feature requests
- **Documentation**: See `.github/copilot-instructions.md` for AI agent guidance
- **Email**: aarnold@godtg.co

## Acknowledgments

- Built with [LangChain](https://github.com/langchain-ai/langchain)
- Vector storage by [ChromaDB](https://www.trychroma.com/)
- Embeddings from [sentence-transformers](https://www.sbert.net/)
- Web framework: [FastAPI](https://fastapi.tiangolo.com/)

---

**Made with ❤️ for better API documentation**
