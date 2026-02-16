"""Inspect how the course schedule is being stored."""
from src.vectorstore.chroma_manager import ChromaManager

chroma = ChromaManager()
collection = chroma.collection

# Get all documents with "Course Schedule" in title
results = collection.get(
    where={"title": "Course Schedule"},
    include=['documents', 'metadatas']
)

print(f"Found {len(results['documents'])} 'Course Schedule' documents\n")

for i, (doc, meta) in enumerate(zip(results['documents'], results['metadatas']), 1):
    print(f"{'='*70}")
    print(f"Document {i}")
    print(f"{'='*70}")
    print(f"Title: {meta.get('title')}")
    print(f"Chunks: {meta.get('chunk_index', 0) + 1} of {meta.get('total_chunks', 1)}")
    print(f"Length: {len(doc)} characters")
    print(f"\nContent preview (first 500 chars):")
    print(doc[:500])
    print(f"\n...middle section...")
    print(f"\nContent preview (chars 1000-1500):")
    print(doc[1000:1500])
    print(f"\n\nFull content:\n{doc}\n")
