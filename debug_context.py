"""Debug what context is being sent to LLM."""
from src.retrieval.retriever import Retriever

retriever = Retriever()
question = "what is on Thu, Mar 12?"

contexts = retriever.retrieve(question, top_k=5)

print(f"Found {len(contexts)} contexts\n")

for i, ctx in enumerate(contexts, 1):
    print(f"{'='*70}")
    print(f"CONTEXT {i}: {ctx['metadata'].get('title')}")
    print(f"Similarity: {ctx['similarity']:.3f}")
    print(f"{'='*70}")
    print(ctx['text'])
    print()

# Check if "Mar 12" appears in any context
for i, ctx in enumerate(contexts, 1):
    if 'Mar 12' in ctx['text']:
        print(f"✅ 'Mar 12' found in context {i}!")
        # Find and print the specific line
        lines = ctx['text'].split('\n')
        for line in lines:
            if 'Mar 12' in line:
                print(f"   Line: {line}")
    else:
        print(f"❌ 'Mar 12' NOT found in context {i}")
