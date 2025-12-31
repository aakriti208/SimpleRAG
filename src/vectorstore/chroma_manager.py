import chromadb
from chromadb.config import Settings
from typing import List, Dict, Optional
from src.config import CHROMA_DB_DIR, CHROMA_COLLECTION_NAME, CHROMA_DISTANCE_METRIC
from src.embedding.embedder import Embedder


class ChromaManager:
    """Manages ChromaDB operations for persistent vector storage."""

    def __init__(self, persist_directory: str = str(CHROMA_DB_DIR),
                 collection_name: str = CHROMA_COLLECTION_NAME):
        self.persist_directory = persist_directory
        self.collection_name = collection_name

        # Initialize ChromaDB client with persistence
        self.client = chromadb.PersistentClient(
            path=self.persist_directory,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )

        # Initialize embedder
        self.embedder = Embedder()

        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": CHROMA_DISTANCE_METRIC}
        )

        print(f"ChromaDB initialized at {self.persist_directory}")
        print(f"Collection '{self.collection_name}' has {self.collection.count()} documents")

    def add_documents(self, chunks: List[Dict], batch_size: int = 100):
        """Add document chunks to ChromaDB."""
        if not chunks:
            print("No chunks to add")
            return

        # Extract texts and metadata
        texts = [chunk["text"] for chunk in chunks]
        # Clean metadata: remove None values (ChromaDB doesn't accept them)
        metadatas = [
            {k: v for k, v in chunk.get("metadata", {}).items() if v is not None and v != ''}
            for chunk in chunks
        ]
        ids = [f"doc_{i}" for i in range(self.collection.count(),
                                          self.collection.count() + len(chunks))]

        print(f"Generating embeddings for {len(texts)} chunks...")
        embeddings = self.embedder.embed_batch(texts, batch_size=batch_size)

        print(f"Adding {len(texts)} documents to ChromaDB...")
        # Add in batches
        for i in range(0, len(texts), batch_size):
            batch_end = min(i + batch_size, len(texts))
            self.collection.add(
                embeddings=embeddings[i:batch_end].tolist(),
                documents=texts[i:batch_end],
                metadatas=metadatas[i:batch_end],
                ids=ids[i:batch_end]
            )
            print(f"Added batch {i//batch_size + 1}/{(len(texts)-1)//batch_size + 1}")

        print(f"Successfully added {len(texts)} documents. Total documents: {self.collection.count()}")

    def query(self, query_text: str, n_results: int = 3,
              where: Optional[Dict] = None) -> Dict:
        """Query ChromaDB for similar documents."""
        # Generate embedding for query
        query_embedding = self.embedder.embed_text(query_text)

        # Query collection
        results = self.collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=n_results,
            where=where
        )

        return results

    def delete_collection(self):
        """Delete the current collection."""
        self.client.delete_collection(name=self.collection_name)
        print(f"Deleted collection '{self.collection_name}'")

    def reset_collection(self):
        """Reset the collection (delete and recreate)."""
        self.delete_collection()
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": CHROMA_DISTANCE_METRIC}
        )
        print(f"Reset collection '{self.collection_name}'")

    def add_documents_with_ids(self, chunks: List[Dict], ids: List[str],
                               batch_size: int = 100):
        """
        Add document chunks with custom IDs for update support.

        Args:
            chunks: List of chunk dicts with 'text' and 'metadata'
            ids: List of custom IDs corresponding to chunks
            batch_size: Number of chunks to process per batch
        """
        if not chunks or len(chunks) != len(ids):
            print(f"Invalid input: {len(chunks)} chunks, {len(ids)} IDs")
            return

        # Extract texts and metadata
        texts = [chunk["text"] for chunk in chunks]
        # Clean metadata: remove None values (ChromaDB doesn't accept them)
        metadatas = [
            {k: v for k, v in chunk.get("metadata", {}).items() if v is not None and v != ''}
            for chunk in chunks
        ]

        print(f"Generating embeddings for {len(texts)} chunks...")
        embeddings = self.embedder.embed_batch(texts, batch_size=batch_size)

        print(f"Adding {len(texts)} documents to ChromaDB...")
        # Add in batches
        for i in range(0, len(texts), batch_size):
            batch_end = min(i + batch_size, len(texts))
            self.collection.add(
                embeddings=embeddings[i:batch_end].tolist(),
                documents=texts[i:batch_end],
                metadatas=metadatas[i:batch_end],
                ids=ids[i:batch_end]
            )
            print(f"Added batch {i//batch_size + 1}/{(len(texts)-1)//batch_size + 1}")

        print(f"Successfully added {len(texts)} documents. Total documents: {self.collection.count()}")

    def delete_by_content_id(self, content_id: str):
        """
        Delete all chunks for a specific content item.

        Args:
            content_id: The content ID to delete
        """
        try:
            # Generate all possible chunk IDs for this content
            # Assuming max 100 chunks per content item
            chunk_ids = [f"{content_id}_chunk_{i}" for i in range(100)]

            # Delete (ignores non-existent IDs)
            self.collection.delete(ids=chunk_ids)
            print(f"Deleted chunks for content_id: {content_id}")
        except Exception as e:
            print(f"Error deleting content_id {content_id}: {e}")

    def update_content(self, content_id: str, new_chunks: List[Dict]):
        """
        Update content by deleting old chunks and adding new ones.

        Args:
            content_id: Content ID to update
            new_chunks: New chunks to add
        """
        # Delete old chunks
        self.delete_by_content_id(content_id)

        # Add new chunks
        chunk_ids = [
            f"{content_id}_chunk_{chunk['metadata']['chunk_index']}"
            for chunk in new_chunks
        ]
        self.add_documents_with_ids(new_chunks, chunk_ids)

    def get_collection_stats(self) -> Dict:
        """Get statistics about the collection."""
        return {
            "name": self.collection_name,
            "count": self.collection.count(),
            "persist_directory": self.persist_directory
        }
