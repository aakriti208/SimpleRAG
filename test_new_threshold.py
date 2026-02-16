"""Test the new retrieval threshold."""
import sys
# Force reload of config
if 'src.config' in sys.modules:
    del sys.modules['src.config']

from src.config import SIMILARITY_THRESHOLD, TOP_K_RESULTS
from src.retrieval.retriever import Retriever

print(f"\n{'='*70}")
print(f"CONFIGURATION CHECK")
print('='*70)
print(f"SIMILARITY_THRESHOLD: {SIMILARITY_THRESHOLD}")
print(f"TOP_K_RESULTS: {TOP_K_RESULTS}")

retriever = Retriever()
stats = retriever.get_stats()
print(f"Total documents in ChromaDB: {stats['count']}")

print(f"\n{'='*70}")
print(f"TEST QUERY: 'course schedule'")
print('='*70)

results = retriever.retrieve("course schedule", top_k=10)

print(f"\nResults after filtering (threshold={SIMILARITY_THRESHOLD}):")
print(f"Found {len(results)} results\n")

for i, ctx in enumerate(results, 1):
    print(f"[{i}] Similarity: {ctx['similarity']:.3f}")
    print(f"    Title: {ctx['metadata'].get('title', 'N/A')}")
    print(f"    Type: {ctx['metadata'].get('content_type', 'N/A')}")
    print(f"    Preview: {ctx['text'][:100]}...")
    print()

if len(results) > 0:
    print("✅ SUCCESS: Course schedule content is now being retrieved!")
else:
    print("❌ PROBLEM: Still no results found")
