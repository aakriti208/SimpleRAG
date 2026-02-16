"""Final test of the improved RAG system."""
from rag_demo import demo_rag

print("\n" + "="*70)
print("TESTING IMPROVED RAG SYSTEM")
print("="*70)

# Test the problematic question
question = "What is the course schedule?"
print(f"\nQuestion: {question}\n")

demo_rag(question, show_stats=True)
