# OpenAPI MCP - RAG System for OpenAPI Specifications

A local Retrieval-Augmented Generation (RAG) system that ingests OpenAPI specifications and exposes them via an MCP server for IDE integration.

## Project Status

🚧 **In Development** - Basic project structure has been set up.

## Quick Start

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies (coming soon)
pip install -r requirements.txt

# Copy environment configuration
cp .env.example .env
```

## Project Structure

```
/open-api-mcp/
├── .github/
│   └── copilot-instructions.md  # AI agent instructions
├── api_specs/                    # OpenAPI JSON files
├── vector_store/                 # Vector database (gitignored)
├── venv/                         # Python virtual environment
├── config.py                     # Configuration management
├── .env.example                  # Environment variables template
├── .gitignore
└── README.md
```

## Architecture

The system has two main components:

1. **Ingestion** (`ingest.py` - coming soon): Processes OpenAPI specs, creates embeddings, stores in vector database
2. **Querying** (`query.py` and `server.py` - coming soon): Retrieves context for AI assistants

## Development

See [rag_plan.md](rag_plan.md) for the complete implementation plan.

Track development progress with beads:
```bash
bd ready     # See available tasks
bd list      # View all issues
```
