"""
RAG Demo - Now powered by ChromaDB!

This replaces the old in-memory knowledge base with persistent vector storage.
Run test_with_sample_data.py first to populate ChromaDB with sample data.
"""
from src.retrieval.retriever import Retriever
from src.generation.generator import Generator


def demo_rag(question: str, show_stats: bool = True):
    """
    Run RAG demo comparing with and without RAG.

    Args:
        question: User's question
        show_stats: Whether to show retrieval statistics
    """
    retriever = Retriever()
    generator = Generator()

    print("\n" + "="*70)
    print("WITHOUT RAG:")
    print("="*70)
    answer_without = generator.generate_without_rag(question)
    print(answer_without)

    print("\n" + "="*70)
    print("WITH RAG:")
    print("="*70)

    # Retrieve contexts from ChromaDB (semantic search!)
    retrieved_contexts = retriever.retrieve(question, top_k=5)

    if retrieved_contexts:
        print(f"\nRetrieved {len(retrieved_contexts)} relevant contexts:\n")
        for i, ctx in enumerate(retrieved_contexts, 1):
            similarity = ctx['similarity']
            title = ctx['metadata'].get('title', 'Unknown')
            print(f"[{i}] {title} (Similarity: {similarity:.3f})")
            if show_stats:
                source = ctx['metadata'].get('source', 'Unknown')
                print(f"    Source: {source}")
                print(f"    Preview: {ctx['text'][:80]}...")
            print()
    else:
        print("No relevant context found in knowledge base\n")

    # Generate answer with RAG
    answer_with, kb_context, llm_context = generator.generate_with_rag(
        question, retrieved_contexts
    )

    print("LLM General Knowledge Context:")
    print(llm_context)

    print("\n" + "-"*70)
    print("FINAL ANSWER:")
    print("-"*70)
    print(answer_with)



def main():
    # Check if ChromaDB has data
    retriever = Retriever()
    stats = retriever.get_stats()

    if stats['count'] == 0:
        print("\n⚠️  ChromaDB is empty!")
        return

    print(f"\nKnowledge Base: {stats['count']} documents ready")

    question = input("Ask a question: ")
    demo_rag(question, show_stats=True)


if __name__ == "__main__":
    main()
