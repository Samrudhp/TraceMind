"""ChromaDB client wrapper for TraceMind."""
import uuid
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings
from chromadb.api.models.Collection import Collection
import numpy as np


class ChromaService:
    """Service for interacting with ChromaDB."""
    
    def __init__(self, persist_directory: str = "./chroma_db"):
        """Initialize ChromaDB client.
        
        Args:
            persist_directory: Directory for persistent storage
        """
        print(f"Initializing ChromaDB at: {persist_directory}")
        self.client = chromadb.Client(
            Settings(
                chroma_db_impl="duckdb+parquet",
                persist_directory=persist_directory,
                anonymized_telemetry=False
            )
        )
        self.collection_name = "memories"
        self.collection = self._get_or_create_collection()
        print(f"Collection '{self.collection_name}' ready with {self.collection.count()} items")
    
    def _get_or_create_collection(self) -> Collection:
        """Get or create the memories collection."""
        return self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"description": "TraceMind memories"}
        )
    
    def add_memory(
        self,
        text: str,
        embedding: np.ndarray,
        metadata: Dict[str, Any]
    ) -> str:
        """Add a new memory to the collection.
        
        Args:
            text: Memory text content
            embedding: Vector embedding
            metadata: Metadata dict
            
        Returns:
            UUID of the created memory
        """
        memory_id = str(uuid.uuid4())
        
        self.collection.add(
            ids=[memory_id],
            documents=[text],
            embeddings=[embedding.tolist()],
            metadatas=[metadata]
        )
        
        return memory_id
    
    def query_memories(
        self,
        query_embedding: np.ndarray,
        n_results: int = 10,
        where: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Query memories by embedding similarity.
        
        Args:
            query_embedding: Query vector
            n_results: Number of results to return
            where: Metadata filter dict
            
        Returns:
            Query results from ChromaDB
        """
        results = self.collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=n_results,
            where=where,
            include=["documents", "metadatas", "embeddings", "distances"]
        )
        return results
    
    def get_all_memories(self, limit: Optional[int] = None) -> Dict[str, Any]:
        """Get all memories from the collection.
        
        Args:
            limit: Optional limit on number of results
            
        Returns:
            All memories with embeddings and metadata
        """
        result = self.collection.get(
            include=["documents", "metadatas", "embeddings"],
            limit=limit
        )
        return result
    
    def delete_memories(self, ids: List[str]):
        """Delete memories by IDs.
        
        Args:
            ids: List of memory IDs to delete
        """
        if ids:
            self.collection.delete(ids=ids)
    
    def update_memory(
        self,
        memory_id: str,
        document: Optional[str] = None,
        embedding: Optional[np.ndarray] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Update an existing memory.
        
        Args:
            memory_id: ID of memory to update
            document: New document text (optional)
            embedding: New embedding (optional)
            metadata: New metadata (optional)
        """
        update_args = {"ids": [memory_id]}
        
        if document is not None:
            update_args["documents"] = [document]
        if embedding is not None:
            update_args["embeddings"] = [embedding.tolist()]
        if metadata is not None:
            update_args["metadatas"] = [metadata]
        
        self.collection.update(**update_args)
    
    def count(self) -> int:
        """Get total number of memories."""
        return self.collection.count()
    
    def list_collections(self) -> List[Dict[str, Any]]:
        """List all ChromaDB collections with metadata.
        
        Returns:
            List of collection info dicts
        """
        collections = self.client.list_collections()
        return [
            {
                "name": col.name,
                "count": col.count(),
                "metadata": col.metadata
            }
            for col in collections
        ]
    
    def get_collection_sample(
        self,
        collection_name: str,
        n: int = 20
    ) -> Dict[str, Any]:
        """Get sample documents from a collection.
        
        Args:
            collection_name: Name of collection
            n: Number of samples
            
        Returns:
            Sample documents with metadata and embedding previews
        """
        col = self.client.get_collection(collection_name)
        result = col.get(
            include=["documents", "metadatas", "embeddings"],
            limit=n
        )
        
        # Truncate embeddings for preview
        if result.get("embeddings"):
            result["embedding_previews"] = [
                emb[:8] for emb in result["embeddings"]
            ]
            # Remove full embeddings from response to reduce size
            result["embedding_dimension"] = len(result["embeddings"][0]) if result["embeddings"] else 0
            del result["embeddings"]
        
        return result
    
    def clear_collection(self):
        """Delete and recreate the collection (for testing)."""
        self.client.delete_collection(self.collection_name)
        self.collection = self._get_or_create_collection()


# Global instance
_chroma_service = None


def get_chroma_service() -> ChromaService:
    """Get or create the global ChromaDB service instance."""
    global _chroma_service
    if _chroma_service is None:
        _chroma_service = ChromaService()
    return _chroma_service
