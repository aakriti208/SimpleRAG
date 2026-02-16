"""Debug script to test retrieval and see what's in the database."""
from src.retrieval.retriever import Retriever
from src.vectorstore.chroma_manager import ChromaManager

def debug_query(query: str):
    """Test a query and see what gets retrieved."""
    retriever = Retriever()
    chroma = ChromaManager()

    print(f"\n{'='*70}")
    print(f"QUERY: {query}")
    print('='*70)

    # Get raw results without filtering
    raw_results = chroma.query(query_text=query, n_results=10)

    print(f"\nRaw results count: {len(raw_results['documents'][0]) if raw_results['documents'] else 0}")

    if raw_results['documents'] and raw_results['documents'][0]:
        for i in range(len(raw_results['documents'][0])):
            doc = raw_results['documents'][0][i]
            metadata = raw_results['metadatas'][0][i]
            distance = raw_results['distances'][0][i]
            similarity = 1 - distance

            print(f"\n[{i+1}] Similarity: {similarity:.3f} | Distance: {distance:.3f}")
            print(f"    Title: {metadata.get('title', 'N/A')}")
            print(f"    Type: {metadata.get('content_type', 'N/A')}")
            print(f"    Course: {metadata.get('course_name', 'N/A')}")
            print(f"    Content preview: {doc[:150]}...")

    # Now test with retriever (which filters by threshold)
    print(f"\n{'='*70}")
    print("AFTER THRESHOLD FILTERING (0.4):")
    print('='*70)

    filtered = retriever.retrieve(query, top_k=10)
    print(f"\nFiltered results: {len(filtered)}")

    for i, ctx in enumerate(filtered, 1):
        print(f"\n[{i}] Similarity: {ctx['similarity']:.3f}")
        print(f"    Title: {ctx['metadata'].get('title', 'N/A')}")
        print(f"    Type: {ctx['metadata'].get('content_type', 'N/A')}")

def sample_content():
    """Show sample content from database."""
    chroma = ChromaManager()
    stats = chroma.get_collection_stats()

    print(f"\n{'='*70}")
    print(f"DATABASE STATS")
    print('='*70)
    print(f"Total documents: {stats['count']}")

    # Get sample documents
    collection = chroma.collection
    sample = collection.get(limit=10, include=['documents', 'metadatas'])

    print(f"\n{'='*70}")
    print(f"SAMPLE DOCUMENTS (showing 10):")
    print('='*70)

    if sample['documents']:
        for i, (doc, meta) in enumerate(zip(sample['documents'], sample['metadatas']), 1):
            print(f"\n[{i}] Title: {meta.get('title', 'N/A')}")
            print(f"    Type: {meta.get('content_type', 'N/A')}")
            print(f"    Course: {meta.get('course_name', 'N/A')}")
            print(f"    Content: {doc[:200]}...")

if __name__ == "__main__":
    # Show database overview
    sample_content()

    # Test queries
    print("\n\n" + "="*70)
    print("TESTING RETRIEVAL")
    print("="*70)

    debug_query("course schedule")
    debug_query("what is the schedule")
    debug_query("weekly topics")
    debug_query("syllabus")
