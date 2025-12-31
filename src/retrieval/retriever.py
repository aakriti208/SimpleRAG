from typing import List, Dict, Optional
from src.vectorstore.chroma_manager import ChromaManager
from src.config import TOP_K_RESULTS, SIMILARITY_THRESHOLD


class Retriever:
    """Handles retrieval operations using ChromaDB."""

    def __init__(self):
        self.chroma_manager = ChromaManager()

    def retrieve(self, question: str, top_k: int = TOP_K_RESULTS,
                 course_filter: Optional[str] = None) -> List[Dict]:
        """
        Retrieve relevant context for a question.

        Returns list of dicts with 'text', 'metadata', and 'distance' keys.
        """
        # Build metadata filter if course specified
        where_filter = None
        if course_filter:
            where_filter = {"course_id": course_filter}

        # Query ChromaDB
        results = self.chroma_manager.query(
            query_text=question,
            n_results=top_k,
            where=where_filter
        )

        # Format results
        retrieved_contexts = []
        if results['documents'] and len(results['documents'][0]) > 0:
            for i in range(len(results['documents'][0])):
                distance = results['distances'][0][i]
                # Convert distance to similarity (for cosine: similarity = 1 - distance)
                similarity = 1 - distance

                # Filter by threshold
                if similarity >= SIMILARITY_THRESHOLD:
                    context = {
                        'text': results['documents'][0][i],
                        'metadata': results['metadatas'][0][i],
                        'similarity': similarity,
                        'distance': distance
                    }
                    retrieved_contexts.append(context)

        return retrieved_contexts

    def get_stats(self) -> Dict:
        """Get collection statistics."""
        return self.chroma_manager.get_collection_stats()
