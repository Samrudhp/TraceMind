"""Memory compaction and decay logic."""
from typing import List, Dict, Any, Set, Tuple
from datetime import datetime
import numpy as np
from collections import defaultdict

from ..utils import (
    calculate_age_days,
    cosine_similarity,
    get_utc_now,
    to_iso_string,
    MergeLogger
)


class CompactionService:
    """Handles memory compaction and redundancy elimination."""
    
    # Configuration parameters
    SIM_THRESHOLD = 0.92
    MIN_IMPORTANCE_KEEP = 0.2
    MAX_CLUSTER_SIZE = 10
    DECAY_RATE = 0.01
    DELETE_SIMILARITY_THRESHOLD = 0.88
    DELETE_AGE_THRESHOLD_DAYS = 30
    
    def __init__(self, chroma_service, embedding_service):
        """Initialize compaction service.
        
        Args:
            chroma_service: ChromaDB service instance
            embedding_service: Embedding service instance
        """
        self.chroma = chroma_service
        self.embeddings = embedding_service
        self.merge_logger = MergeLogger()
    
    def run_compaction(self) -> Dict[str, Any]:
        """Run full compaction cycle.
        
        Returns:
            Statistics about the compaction run
        """
        print("Starting compaction...")
        before_count = self.chroma.count()
        
        # Fetch all memories
        all_data = self.chroma.get_all_memories()
        
        if not all_data["ids"] or len(all_data["ids"]) < 2:
            print("Not enough memories to compact")
            return {
                "before_count": before_count,
                "after_count": before_count,
                "clusters_merged": 0,
                "items_deleted": 0,
                "merge_events": [],
                "timestamp": to_iso_string(get_utc_now())
            }
        
        # Build clusters
        clusters = self._build_clusters(
            all_data["ids"],
            all_data["embeddings"],
            all_data["metadatas"]
        )
        
        print(f"Found {len(clusters)} clusters to merge")
        
        # Merge clusters
        merge_events = []
        for cluster in clusters:
            if len(cluster["ids"]) < 2:
                continue
            
            merged_id = self._merge_cluster(cluster)
            
            event = {
                "timestamp": to_iso_string(get_utc_now()),
                "cluster_size": len(cluster["ids"]),
                "merged_ids": cluster["ids"],
                "new_id": merged_id,
                "representative_text": cluster["documents"][0][:100]
            }
            merge_events.append(event)
            self.merge_logger.log_merge(event)
        
        # Delete low-importance old redundant memories
        deleted_count = self._delete_redundant_memories(all_data)
        
        after_count = self.chroma.count()
        
        stats = {
            "before_count": before_count,
            "after_count": after_count,
            "clusters_merged": len(merge_events),
            "items_deleted": deleted_count,
            "merge_events": merge_events,
            "timestamp": to_iso_string(get_utc_now())
        }
        
        print(f"Compaction complete: {before_count} -> {after_count} memories")
        return stats
    
    def _build_clusters(
        self,
        ids: List[str],
        embeddings: List[List[float]],
        metadatas: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Build clusters of similar memories using single-linkage.
        
        Args:
            ids: List of memory IDs
            embeddings: List of embedding vectors
            metadatas: List of metadata dicts
            
        Returns:
            List of cluster dicts
        """
        n = len(ids)
        embeddings_np = np.array(embeddings)
        
        # Track which items are already in a cluster
        clustered = set()
        clusters = []
        
        for i in range(n):
            if ids[i] in clustered:
                continue
            
            # Start new cluster with item i
            cluster_ids = [ids[i]]
            cluster_embeddings = [embeddings_np[i]]
            cluster_docs = [self.chroma.collection.get(ids=[ids[i]])["documents"][0]]
            cluster_metadatas = [metadatas[i]]
            
            # Find similar items for single-linkage clustering
            for j in range(i + 1, n):
                if ids[j] in clustered:
                    continue
                
                # Check similarity with all items in current cluster
                for cluster_emb in cluster_embeddings:
                    sim = cosine_similarity(embeddings_np[j], cluster_emb)
                    
                    if sim >= self.SIM_THRESHOLD:
                        cluster_ids.append(ids[j])
                        cluster_embeddings.append(embeddings_np[j])
                        cluster_docs.append(
                            self.chroma.collection.get(ids=[ids[j]])["documents"][0]
                        )
                        cluster_metadatas.append(metadatas[j])
                        clustered.add(ids[j])
                        break
                
                # Limit cluster size
                if len(cluster_ids) >= self.MAX_CLUSTER_SIZE:
                    break
            
            # Only keep clusters with multiple items
            if len(cluster_ids) >= 2:
                clustered.update(cluster_ids)
                clusters.append({
                    "ids": cluster_ids,
                    "embeddings": cluster_embeddings,
                    "documents": cluster_docs,
                    "metadatas": cluster_metadatas
                })
        
        return clusters
    
    def _merge_cluster(self, cluster: Dict[str, Any]) -> str:
        """Merge a cluster into a single memory.
        
        Args:
            cluster: Cluster dict with ids, embeddings, documents, metadatas
            
        Returns:
            ID of the newly created merged memory
        """
        ids = cluster["ids"]
        embeddings = cluster["embeddings"]
        documents = cluster["documents"]
        metadatas = cluster["metadatas"]
        
        # Calculate weights based on importance and recency
        weights = []
        for meta in metadatas:
            age_days = calculate_age_days(meta["timestamp"])
            recency_weight = max(0, 1 - self.DECAY_RATE * age_days)
            weight = meta["importance"] * recency_weight
            weights.append(weight)
        
        weights = np.array(weights)
        if weights.sum() == 0:
            weights = np.ones_like(weights)
        weights = weights / weights.sum()
        
        # Compute weighted average embedding
        embeddings_np = np.array(embeddings)
        merged_embedding = np.sum(embeddings_np * weights[:, np.newaxis], axis=0)
        
        # Normalize
        merged_embedding = merged_embedding / np.linalg.norm(merged_embedding)
        
        # Choose representative text (newest)
        timestamps = [meta["timestamp"] for meta in metadatas]
        newest_idx = timestamps.index(max(timestamps))
        representative_text = documents[newest_idx]
        
        # Aggregate metadata
        merged_metadata = {
            "timestamp": timestamps[newest_idx],
            "importance": max(meta["importance"] for meta in metadatas),
            "source": "compaction",
            "last_merged_at": to_iso_string(get_utc_now()),
            "merge_count": sum(meta.get("merge_count", 0) for meta in metadatas) + len(ids) - 1
        }
        
        # Preserve topic from newest if available
        if "topic" in metadatas[newest_idx]:
            merged_metadata["topic"] = metadatas[newest_idx]["topic"]
        
        # Add merged memory
        new_id = self.chroma.add_memory(
            text=representative_text,
            embedding=merged_embedding,
            metadata=merged_metadata
        )
        
        # Delete original cluster members
        self.chroma.delete_memories(ids)
        
        return new_id
    
    def _delete_redundant_memories(self, all_data: Dict[str, Any]) -> int:
        """Delete low-importance, old, redundant memories.
        
        Args:
            all_data: All memories data from ChromaDB
            
        Returns:
            Number of memories deleted
        """
        to_delete = []
        
        ids = all_data["ids"]
        embeddings = np.array(all_data["embeddings"])
        metadatas = all_data["metadatas"]
        
        for i, (memory_id, meta) in enumerate(zip(ids, metadatas)):
            # Check deletion criteria
            importance = meta.get("importance", 0.5)
            age_days = calculate_age_days(meta["timestamp"])
            
            if (importance < self.MIN_IMPORTANCE_KEEP and 
                age_days > self.DELETE_AGE_THRESHOLD_DAYS):
                
                # Check if there's a similar survivor
                for j, other_emb in enumerate(embeddings):
                    if i == j:
                        continue
                    
                    sim = cosine_similarity(embeddings[i], other_emb)
                    if sim >= self.DELETE_SIMILARITY_THRESHOLD:
                        # Found similar memory, safe to delete this one
                        to_delete.append(memory_id)
                        break
        
        if to_delete:
            self.chroma.delete_memories(to_delete)
        
        return len(to_delete)


# Global instance
_compaction_service = None


def get_compaction_service(chroma_service, embedding_service):
    """Get or create the global compaction service instance."""
    global _compaction_service
    if _compaction_service is None:
        _compaction_service = CompactionService(chroma_service, embedding_service)
    return _compaction_service
