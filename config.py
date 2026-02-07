"""Configuration management for the OpenAPI MCP system."""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Project root directory
PROJECT_ROOT = Path(__file__).parent

# Vector store configuration
VECTOR_STORE_PATH = Path(os.getenv("VECTOR_STORE_PATH", "./vector_store"))
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

# API specs directory
API_SPECS_DIR = Path(os.getenv("API_SPECS_DIR", "./api_specs"))

# MCP Server configuration
MCP_HOST = os.getenv("MCP_HOST", "127.0.0.1")
MCP_PORT = int(os.getenv("MCP_PORT", "8000"))

# Ensure directories exist
VECTOR_STORE_PATH.mkdir(parents=True, exist_ok=True)
API_SPECS_DIR.mkdir(parents=True, exist_ok=True)
