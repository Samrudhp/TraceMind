"""Embedding service using sentence-transformers."""
from typing import List
import numpy as np
from sentence_transformers import SentenceTransformer


class EmbeddingService:
    """Handles text embeddings using sentence-transformers."""
    
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        """Initialize the embedding model.
        
        Args:
            model_name: Name of the sentence-transformers model
        """
        print(f"Loading embedding model: {model_name}")
        self.model = SentenceTransformer(model_name)
        self.dimension = self.model.get_sentence_embedding_dimension()
        print(f"Model loaded. Embedding dimension: {self.dimension}")
    
    def embed(self, texts: List[str]) -> np.ndarray:
        """Generate embeddings for a list of texts.
        
        Args:
            texts: List of text strings to embed
            
        Returns:
            Numpy array of embeddings, shape (len(texts), dimension)
        """
        if not texts:
            return np.array([])
        
        embeddings = self.model.encode(
            texts,
            convert_to_numpy=True,
            show_progress_bar=False,
            normalize_embeddings=True  # Normalize for cosine similarity
        )
        return embeddings
    
    def embed_single(self, text: str) -> np.ndarray:
        """Generate embedding for a single text.
        
        Args:
            text: Text string to embed
            
        Returns:
            Numpy array embedding, shape (dimension,)
        """
        return self.embed([text])[0]


# Global instance (singleton pattern)
_embedding_service = None


def get_embedding_service() -> EmbeddingService:
    """Get or create the global embedding service instance."""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service
