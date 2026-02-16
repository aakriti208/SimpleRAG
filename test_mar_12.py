"""Test the specific question: what is on Thu, Mar 12?"""
from src.retrieval.retriever import Retriever
from src.generation.generator import Generator

retriever = Retriever()
generator = Generator()

question = "what is on Thu, Mar 12?"

print(f"\n{'='*70}")
print(f"QUESTION: {question}")
print('='*70)

# Retrieve contexts
contexts = retriever.retrieve(question, top_k=5)

print(f"\nRetrieved {len(contexts)} contexts:")
for i, ctx in enumerate(contexts, 1):
    print(f"\n[{i}] {ctx['metadata'].get('title')} (Similarity: {ctx['similarity']:.3f})")
    print(f"    Preview: {ctx['text'][:150]}...")

# Generate answer
if contexts:
    answer, kb_context, llm_context = generator.generate_with_rag(question, contexts)

    print(f"\n{'='*70}")
    print("ANSWER WITH RAG:")
    print('='*70)
    print(answer)
else:
    print("\n❌ No contexts retrieved")
