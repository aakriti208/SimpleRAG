#!/usr/bin/env python3
"""
SimpleRAG Web Interface

FastAPI application that provides a web interface for the SimpleRAG system.

"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Dict, Optional
import uvicorn
from pathlib import Path
import logging

from src.retrieval.retriever import Retriever
from src.generation.generator import Generator
from src.config import OLLAMA_BASE_URL

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="SimpleRAG Web Interface",
    version="1.0.0",
    description="Retrieval-Augmented Generation system for Canvas LMS content"
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Singleton instances (initialized on startup)
retriever: Optional[Retriever] = None
generator: Optional[Generator] = None


# Request/Response Models
class QuestionRequest(BaseModel):
    question: str
    top_k: int = 3


class ContextResult(BaseModel):
    text: str
    title: str
    source: str
    similarity: float


class RAGResponse(BaseModel):
    answer_with_rag: str
    answer_without_rag: str
    contexts: List[ContextResult]
    kb_context: str
    llm_context: str
    error: Optional[str] = None


# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize RAG components on application startup."""
    global retriever, generator

    logger.info("Initializing SimpleRAG components...")

    try:
        # Initialize retriever
        retriever = Retriever()
        logger.info("Retriever initialized successfully")

        # Initialize generator
        generator = Generator()
        logger.info("Generator initialized successfully")

        # Check if knowledge base has data
        stats = retriever.get_stats()
        if stats['count'] == 0:
            logger.warning("WARNING: Knowledge base is empty! Please run ingestion first.")
            logger.warning("Run: python scripts/ingest_data.py")
        else:
            logger.info(f"Knowledge base loaded: {stats['count']} documents")

        logger.info(f"Ollama URL: {OLLAMA_BASE_URL}")
        logger.info("SimpleRAG web interface ready!")

    except Exception as e:
        logger.error(f"ERROR during startup: {e}", exc_info=True)
        raise


# Health check endpoint
@app.get("/health")
async def health_check():
    """
    Health check endpoint.

    Returns system status and knowledge base statistics.
    """
    try:
        stats = retriever.get_stats() if retriever else {"count": 0}
        return {
            "status": "healthy",
            "knowledge_base_documents": stats['count'],
            "ollama_url": OLLAMA_BASE_URL
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Main page
@app.get("/", response_class=HTMLResponse)
async def read_root():
    """
    Serve the main HTML page.
    """
    html_file = Path(__file__).parent / "templates" / "index.html"

    if not html_file.exists():
        raise HTTPException(status_code=404, detail="HTML template not found")

    with open(html_file, "r") as f:
        return f.read()


# Query endpoint
@app.post("/query", response_model=RAGResponse)
async def query_rag(request: QuestionRequest):
    """
    Process a question and return RAG-powered answer.

    Args:
        request: QuestionRequest with question and top_k

    Returns:
        RAGResponse with answer, contexts, and additional info
    """
    logger.info(f"Received query: {request.question[:100]}...")

    try:
        # Retrieve contexts
        retrieved_contexts = retriever.retrieve(
            request.question,
            top_k=request.top_k
        )

        logger.info(f"Retrieved {len(retrieved_contexts)} contexts")

        # Generate answer WITHOUT RAG (using only Ollama's knowledge)
        logger.info("Generating answer without RAG...")
        answer_without_rag = generator.generate_without_rag(request.question)

        # Handle no contexts found
        if not retrieved_contexts:
            logger.warning("No relevant contexts found")
            return RAGResponse(
                answer_with_rag="I couldn't find relevant information in the Canvas course materials to answer your question.",
                answer_without_rag=answer_without_rag,
                contexts=[],
                kb_context="No relevant context found",
                llm_context="",
                error="No relevant contexts found"
            )

        # Generate answer WITH RAG (using Canvas materials + Ollama)
        logger.info("Generating answer with RAG...")
        answer_with_rag, kb_context, llm_context = generator.generate_with_rag(
            request.question,
            retrieved_contexts
        )

        logger.info("Both answers generated successfully")

        # Format contexts for response
        formatted_contexts = [
            ContextResult(
                text=ctx['text'],
                title=ctx['metadata'].get('title', 'Unknown'),
                source=ctx['metadata'].get('source', 'Unknown'),
                similarity=ctx['similarity']
            )
            for ctx in retrieved_contexts
        ]

        return RAGResponse(
            answer_with_rag=answer_with_rag,
            answer_without_rag=answer_without_rag,
            contexts=formatted_contexts,
            kb_context=kb_context,
            llm_context=llm_context
        )

    except Exception as e:
        logger.error(f"Error processing query: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# Run server
if __name__ == "__main__":
    logger.info("Starting SimpleRAG web server...")
    logger.info("Navigate to: http://localhost:8000")

    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
