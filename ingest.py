#!/usr/bin/env python3
"""
OpenAPI Ingestion Script

Loads OpenAPI specification files, creates structured documents for each endpoint,
generates embeddings, and stores them in a ChromaDB vector database.
"""

import json
import sys
from pathlib import Path
from typing import List, Dict, Any

from langchain.docstore.document import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

import config


def load_openapi_spec(file_path: Path) -> Dict[str, Any]:
    """Load and parse an OpenAPI JSON specification file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        sys.exit(1)


def create_endpoint_document(
    path: str,
    method: str,
    operation: Dict[str, Any],
    spec_info: Dict[str, Any]
) -> Document:
    """
    Create a LangChain Document for a single API endpoint.
    
    Each document contains:
    - Summary and description
    - Parameters (path, query, header, cookie)
    - Request body schema
    - Response schemas
    - Metadata for filtering and retrieval
    """
    # Extract operation details
    summary = operation.get('summary', '')
    description = operation.get('description', '')
    operation_id = operation.get('operationId', f"{method}_{path}")
    
    # Build parameter documentation
    parameters = []
    if 'parameters' in operation:
        for param in operation['parameters']:
            param_info = {
                'name': param.get('name', ''),
                'in': param.get('in', ''),
                'required': param.get('required', False),
                'description': param.get('description', ''),
                'schema': param.get('schema', {})
            }
            parameters.append(param_info)
    
    # Extract request body
    request_body = {}
    if 'requestBody' in operation:
        req_body = operation['requestBody']
        request_body = {
            'description': req_body.get('description', ''),
            'required': req_body.get('required', False),
            'content': req_body.get('content', {})
        }
    
    # Extract responses
    responses = {}
    if 'responses' in operation:
        for status_code, response in operation['responses'].items():
            responses[status_code] = {
                'description': response.get('description', ''),
                'content': response.get('content', {})
            }
    
    # Create document content
    content_parts = [
        f"API Endpoint: {method.upper()} {path}",
        f"Operation ID: {operation_id}",
        ""
    ]
    
    if summary:
        content_parts.append(f"Summary: {summary}")
    
    if description:
        content_parts.append(f"Description: {description}")
    
    if parameters:
        content_parts.append("\nParameters:")
        for param in parameters:
            required = "required" if param['required'] else "optional"
            content_parts.append(
                f"  - {param['name']} ({param['in']}, {required}): {param['description']}"
            )
    
    if request_body:
        content_parts.append("\nRequest Body:")
        content_parts.append(f"  {request_body['description']}")
        if request_body.get('content'):
            content_parts.append(f"  Content types: {', '.join(request_body['content'].keys())}")
    
    if responses:
        content_parts.append("\nResponses:")
        for status_code, response in responses.items():
            content_parts.append(f"  {status_code}: {response['description']}")
    
    content = "\n".join(content_parts)
    
    # Create metadata for filtering and retrieval
    metadata = {
        'path': path,
        'method': method.upper(),
        'operation_id': operation_id,
        'api_title': spec_info.get('title', ''),
        'api_version': spec_info.get('version', ''),
        'tags': operation.get('tags', []),
        'source': 'openapi_spec'
    }
    
    return Document(page_content=content, metadata=metadata)


def process_openapi_spec(spec: Dict[str, Any]) -> List[Document]:
    """
    Process an OpenAPI specification and create documents for each endpoint.
    
    Args:
        spec: Parsed OpenAPI specification dictionary
        
    Returns:
        List of LangChain Document objects, one per endpoint
    """
    documents = []
    
    # Extract API info
    info = spec.get('info', {})
    
    # Process each path and method
    paths = spec.get('paths', {})
    for path, path_item in paths.items():
        # Process each HTTP method for this path
        for method in ['get', 'post', 'put', 'delete', 'patch', 'options', 'head']:
            if method in path_item:
                operation = path_item[method]
                doc = create_endpoint_document(path, method, operation, info)
                documents.append(doc)
    
    return documents


def ingest_openapi_specs():
    """
    Main ingestion function.
    
    Loads all OpenAPI JSON files from the api_specs directory,
    processes them into documents, generates embeddings, and stores
    them in the ChromaDB vector store.
    """
    print(f"Starting OpenAPI ingestion...")
    print(f"API specs directory: {config.API_SPECS_DIR}")
    print(f"Vector store path: {config.VECTOR_STORE_PATH}")
    
    # Find all JSON files in the api_specs directory
    json_files = list(config.API_SPECS_DIR.glob("*.json"))
    
    if not json_files:
        print(f"No JSON files found in {config.API_SPECS_DIR}")
        print("Please add OpenAPI specification files to the api_specs directory.")
        sys.exit(1)
    
    print(f"Found {len(json_files)} OpenAPI specification file(s)")
    
    # Process all specifications
    all_documents = []
    for json_file in json_files:
        print(f"\nProcessing: {json_file.name}")
        spec = load_openapi_spec(json_file)
        
        # Get API info
        info = spec.get('info', {})
        api_title = info.get('title', 'Unknown API')
        api_version = info.get('version', 'Unknown')
        
        print(f"  API: {api_title} v{api_version}")
        
        # Create documents for each endpoint
        documents = process_openapi_spec(spec)
        print(f"  Created {len(documents)} endpoint documents")
        
        all_documents.extend(documents)
    
    print(f"\nTotal documents created: {len(all_documents)}")
    
    # Initialize embeddings model
    print(f"\nInitializing embeddings model: {config.EMBEDDING_MODEL}")
    embeddings = HuggingFaceEmbeddings(
        model_name=config.EMBEDDING_MODEL,
        model_kwargs={'device': 'cpu'}
    )
    
    # Create and persist vector store
    print(f"Creating ChromaDB vector store at: {config.VECTOR_STORE_PATH}")
    vectorstore = Chroma.from_documents(
        documents=all_documents,
        embedding=embeddings,
        persist_directory=str(config.VECTOR_STORE_PATH)
    )
    
    print(f"\n✓ Ingestion complete!")
    print(f"  Total endpoints indexed: {len(all_documents)}")
    print(f"  Vector store location: {config.VECTOR_STORE_PATH}")
    print(f"\nYou can now use query.py to search the API documentation.")


if __name__ == "__main__":
    ingest_openapi_specs()
