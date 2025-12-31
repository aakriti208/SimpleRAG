# Canvas RAG System

A Retrieval-Augmented Generation (RAG) system that ingests educational content from Canvas LMS and enables intelligent question-answering using semantic search and LLMs.

## What It Does

- **Ingests** all content from Canvas courses (pages, modules, assignments, PDFs, PowerPoints, discussions)
- **Processes** and chunks content for optimal retrieval
- **Stores** in a persistent vector database (ChromaDB) with semantic embeddings
- **Answers** questions using course material via RAG with Ollama

## Prerequisites

- Python 3.11+
- Canvas LMS API token
- Ollama installed and running (for answer generation)

## Setup

### 1. Install Dependencies

```bash
# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install requirements
pip install -r requirements.txt
```

### 2. Configure Environment

Create a `.env` file from the template:

```bash
cp .env.template .env
```

Edit `.env` with your Canvas credentials:

```env
CANVAS_API_TOKEN=your_canvas_api_token_here
CANVAS_BASE_URL=https://canvas.yourinstitution.edu/
CANVAS_COURSE_IDS=course_id1,course_id2
```

### 3. Start Ollama (for answer generation)

```bash
# Install Ollama from https://ollama.ai
# Then start the service
ollama serve

# Pull the model
ollama pull gemma:2b
```

## Usage

### Ingest Canvas Content

**Start with a single content type (recommended for testing):**

```bash
python scripts/ingest_data.py --course YOUR_COURSE_ID --content-type page
```

**Full ingestion (all content types):**

```bash
python scripts/ingest_data.py --course YOUR_COURSE_ID --full
```

**Ingest all configured courses:**

```bash
python scripts/ingest_data.py --full
```

**Incremental update (only new/changed content):**

```bash
python scripts/ingest_data.py --incremental
```

### Query Your Knowledge Base

**Interactive mode:**

```bash
python rag_demo.py
```

**Example questions:**
- "What is this course about?"
- "Explain text preprocessing"
- "What are the assignments in this course?"
- "Tell me about the syllabus"

## Verify Your Data

**Check what's in your knowledge base:**

```bash
python scripts/verify_canvas_data.py
```

Shows:
- Total documents
- Content types (pages, modules, files, etc.)
- Sample content previews
- Recommendations

**Test retrieval only:**

```bash
python test_retrieval_only.py
```

## Project Structure

```
SimpleRAG/
├── src/
│   ├── config.py                    # Configuration management
│   ├── embedding/
│   │   └── embedder.py             # Text → vector embeddings
│   ├── vectorstore/
│   │   └── chroma_manager.py       # ChromaDB operations
│   ├── retrieval/
│   │   └── retriever.py            # Semantic search
│   ├── generation/
│   │   └── generator.py            # LLM answer generation
│   └── ingestion/
│       ├── canvas_client.py        # Canvas API wrapper
│       ├── document_processor.py   # Text extraction & chunking
│       ├── metadata_tracker.py     # Incremental update tracking
│       └── content_handlers/       # Canvas content type handlers
│           ├── page_handler.py
│           ├── module_handler.py
│           ├── assignment_handler.py
│           ├── announcement_handler.py
│           ├── discussion_handler.py
│           └── file_handler.py
├── scripts/
│   ├── ingest_data.py              # Main ingestion script
│   └── verify_canvas_data.py       # Data verification tool
├── data/
│   ├── chroma_db/                  # Vector database (persistent)
│   ├── metadata/                   # Ingestion tracking
│   └── logs/                       # Ingestion logs
└── rag_demo.py                     # Interactive Q&A interface
```

## Key Features

### Ingestion Pipeline

- **Multi-format support:** Pages, Modules, Assignments, PDFs, PowerPoints, Discussions
- **Incremental updates:** Only processes new/changed content
- **Smart chunking:** 500-word chunks with 50-word overlap
- **Rich metadata:** Course, title, type, dates, source links
- **Rate limiting:** Automatic Canvas API throttling
- **Error resilience:** Retries, fallbacks, comprehensive logging

### Retrieval System

- **Semantic search:** Finds content by meaning, not just keywords
- **Similarity scoring:** Ranks results by relevance (0-1 scale)
- **Metadata filtering:** Filter by course, content type, etc.
- **Configurable threshold:** Control result quality

### RAG Generation

- **Context-aware:** Answers based on your course material
- **Source attribution:** Shows which documents were used
- **Ollama integration:** Local LLM (privacy-preserving)

## Configuration Options

Edit `.env` to customize:

```env
# Retrieval settings
TOP_K_RESULTS=3                    # Number of results to retrieve
SIMILARITY_THRESHOLD=0.5           # Minimum similarity score (0-1)

# Chunking settings
CHUNK_SIZE=500                     # Words per chunk
CHUNK_OVERLAP=50                   # Overlapping words between chunks

# Embedding model
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

# LLM settings
OLLAMA_MODEL=gemma:2b
OLLAMA_BASE_URL=http://localhost:11434

# Ingestion settings
MAX_FILE_SIZE_MB=50                # Skip files larger than this
PDF_EXTRACTION_TIMEOUT=30          # Seconds
```

## Testing the Pipeline

### Test 1: Single Content Type
```bash
python scripts/ingest_data.py --course COURSE_ID --content-type page
python scripts/verify_canvas_data.py
```

### Test 2: Full Ingestion
```bash
python scripts/ingest_data.py --course COURSE_ID --full
```

### Test 3: Retrieval
```bash
python test_retrieval_only.py
```

### Test 4: End-to-End RAG
```bash
python rag_demo.py
# Ask: "What is this course about?"
```

### Test 5: Incremental Updates
```bash
# Run twice - second run should skip unchanged content
python scripts/ingest_data.py --incremental
python scripts/ingest_data.py --incremental  # Should process 0 new items
```

## Common Commands

**Reset everything and start fresh:**

```bash
python scripts/ingest_data.py --reset --full
```

**Ingest specific content types:**

```bash
python scripts/ingest_data.py --course COURSE_ID --content-type page module assignment
```

**Check logs:**

```bash
tail -f data/logs/ingestion_*.log
```

## Troubleshooting

**"Content not found" errors**
- Verify Canvas API token is correct in `.env`
- Check course IDs are accessible with your token

**"No text extracted from PDF"**
- Some PDFs are image-based (scanned) and can't be processed
- Check PDF file size (must be < 50MB)

**"No relevant contexts found"**
- Lower `SIMILARITY_THRESHOLD` in `.env` (try 0.3-0.4)
- Verify content was ingested: `python scripts/verify_canvas_data.py`

**"Rate limited by Canvas"**
- Pipeline automatically waits and retries
- Check `INGEST_RATE_LIMIT_THRESHOLD` setting

**Ollama connection failed**
- Ensure Ollama is running: `ollama serve`
- Check `OLLAMA_BASE_URL` in `.env`

## Maintenance

**Daily automated updates (cron):**

```bash
# Add to crontab
0 2 * * * cd /path/to/SimpleRAG && source venv/bin/activate && python scripts/ingest_data.py --incremental
```

**Weekly verification:**

```bash
python scripts/verify_canvas_data.py
```

**Quarterly full re-ingestion:**

```bash
python scripts/ingest_data.py --reset --full
```

## Architecture

```
Canvas API → CanvasClient → ContentHandlers → DocumentProcessor → Embedder → ChromaDB
              (fetch)          (extract)         (clean/chunk)    (vectorize)  (store)

User Query → Embedder → ChromaDB → Retriever → Generator → Answer
            (vectorize)  (search)    (rank)     (LLM)
```

## License

MIT License - See LICENSE file for details

## Support

For issues or questions, check the logs in `data/logs/` or review the verification output:

```bash
python scripts/verify_canvas_data.py
```
