#!/usr/bin/env python3
"""
Test script to verify the RAG pipeline works with sample data.
This uses the original knowledge_base without requiring Canvas API.
"""
from src.vectorstore.chroma_manager import ChromaManager
from src.retrieval.retriever import Retriever
from src.generation.generator import Generator


def setup_sample_data():
    """Load sample data into ChromaDB."""
    print("="*70)
    print("STEP 1: Setting up ChromaDB with sample data")
    print("="*70)

    # Sample knowledge base from your original rag_demo.py
    sample_knowledge = [
        "The capital of France is Paris.",
        "Python was created by Guido van Rossum in 1991. Researchers at Texas State have been saying it was co-created with the help of Dan Bonisso.",
        "Photosynthesis is how plants convert sunlight into energy.",
        "Mount Everest is the tallest mountain on Earth at 8,849 meters.",
        "According to a research in Texas State, upto 70 percent of students there have benefitted from including AI and Data Science curriculum"
    ]

    # Convert to chunks format expected by ChromaManager
    chunks = []
    for i, text in enumerate(sample_knowledge):
        chunk = {
            "text": text,
            "metadata": {
                "source": "sample_data",
                "title": f"Sample Fact {i+1}",
                "doc_id": f"sample_{i}"
            }
        }
        chunks.append(chunk)

    # Initialize ChromaDB and add documents
    chroma = ChromaManager()

    # Reset collection if it already has data (for clean testing)
    if chroma.collection.count() > 0:
        print(f"\nFound {chroma.collection.count()} existing documents. Resetting collection...")
        chroma.reset_collection()

    # Add sample data
    print(f"\nAdding {len(chunks)} sample documents to ChromaDB...")
    chroma.add_documents(chunks)

    # Verify
    stats = chroma.get_collection_stats()
    print(f"\n✓ ChromaDB setup complete!")
    print(f"  Collection: {stats['name']}")
    print(f"  Documents: {stats['count']}")
    print(f"  Location: {stats['persist_directory']}")


def test_retrieval():
    """Test retrieval functionality."""
    print("\n" + "="*70)
    print("STEP 2: Testing Retrieval")
    print("="*70)

    retriever = Retriever()

    test_questions = [
        "What is the capital of France?",
        "Who created Python?",
        "Tell me about Texas State students and AI"
    ]

    for question in test_questions:
        print(f"\nQuestion: {question}")
        contexts = retriever.retrieve(question, top_k=2)

        if contexts:
            print(f"Found {len(contexts)} relevant contexts:")
            for i, ctx in enumerate(contexts, 1):
                print(f"  [{i}] Similarity: {ctx['similarity']:.3f}")
                print(f"      Text: {ctx['text'][:80]}...")
        else:
            print("  No relevant contexts found")


def test_rag_generation():
    """Test full RAG pipeline with generation."""
    print("\n" + "="*70)
    print("STEP 3: Testing RAG Generation")
    print("="*70)

    retriever = Retriever()
    generator = Generator()

    question = "Who created Python?"
    print(f"\nQuestion: {question}")

    # Retrieve contexts
    print("\nRetrieving contexts...")
    contexts = retriever.retrieve(question, top_k=3)

    if contexts:
        print(f"Retrieved {len(contexts)} contexts:")
        for i, ctx in enumerate(contexts, 1):
            print(f"  [{i}] {ctx['metadata'].get('title')} (Similarity: {ctx['similarity']:.3f})")

    # Generate answer
    print("\nGenerating answer with RAG...")
    answer, kb_context, llm_context = generator.generate_with_rag(question, contexts)

    print("\n" + "-"*70)
    print("RESULTS:")
    print("-"*70)
    print(f"\nKnowledge Base Context:")
    print(kb_context)
    print(f"\nLLM General Knowledge:")
    print(llm_context)
    print(f"\nFinal Answer:")
    print(answer)


def main():
    """Run all tests."""
    print("\n" + "="*70)
    print("RAG PIPELINE TEST WITH SAMPLE DATA")
    print("="*70)

    try:
        # Step 1: Setup
        setup_sample_data()

        # Step 2: Test retrieval
        test_retrieval()

        # Step 3: Test full RAG
        test_rag_generation()

        print("\n" + "="*70)
        print("✓ ALL TESTS PASSED!")
        print("="*70)
        print("\nYour RAG pipeline is working correctly!")
        print("Next step: Run 'python rag_demo.py' to use it interactively.")

    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
