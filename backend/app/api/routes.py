"""API routes for TraceMind."""
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
import numpy as np
from sklearn.decomposition import PCA
import umap

from ..models import (
    MemoryInput,
    MemoryResponse,
    RecallResult,
    CollectionInfo,
    CompactionStats,
    StatsResponse
)
from ..services.embeddings import get_embedding_service
from ..services.chroma_client import get_chroma_service
from ..services.compaction import get_compaction_service
from ..utils import (
    create_metadata,
    calculate_age_days,
    cosine_similarity,
    to_iso_string,
    get_utc_now,
    MergeLogger
)

router = APIRouter()

# Service instances
embedding_service = None
chroma_service = None
compaction_service = None
merge_logger = MergeLogger()


def init_services():
    """Initialize service instances."""
    global embedding_service, chroma_service, compaction_service
    if embedding_service is None:
        embedding_service = get_embedding_service()
        chroma_service = get_chroma_service()
        compaction_service = get_compaction_service(chroma_service, embedding_service)


@router.post("/remember", response_model=MemoryResponse)
async def remember(memory: MemoryInput):
    """Store a new memory.
    
    Args:
        memory: Memory input with text, topic, importance
        
    Returns:
        Memory ID and status
    """
    init_services()
    
    try:
        # Generate embedding
        embedding = embedding_service.embed_single(memory.text)
        
        # Create metadata
        metadata = create_metadata(
            importance=memory.importance,
            topic=memory.topic,
            source=memory.source
        )
        
        # Store in ChromaDB
        memory_id = chroma_service.add_memory(
            text=memory.text,
            embedding=embedding,
            metadata=metadata
        )
        
        return MemoryResponse(
            id=memory_id,
            status="stored",
            timestamp=metadata["timestamp"]
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error storing memory: {str(e)}")


@router.get("/recall", response_model=List[RecallResult])
async def recall(
    q: str = Query(..., description="Query text"),
    k: int = Query(5, ge=1, le=50, description="Number of results"),
    decay: bool = Query(True, description="Apply temporal decay"),
    topic: Optional[str] = Query(None, description="Filter by topic")
):
    """Recall memories based on query.
    
    Args:
        q: Query text
        k: Number of results to return
        decay: Whether to apply temporal decay
        topic: Optional topic filter
        
    Returns:
        List of recall results with scores
    """
    init_services()
    
    try:
        # Generate query embedding
        query_embedding = embedding_service.embed_single(q)
        
        # Oversample for reranking
        k_raw = min(k * 2, 100)
        
        # Build metadata filter
        where_filter = {"topic": topic} if topic else None
        
        # Query ChromaDB
        results = chroma_service.query_memories(
            query_embedding=query_embedding,
            n_results=k_raw,
            where=where_filter
        )
        
        if not results["ids"][0]:
            return []
        
        # Rerank with temporal decay and importance
        scored_results = []
        alpha = 0.7  # Weight for recency vs importance
        decay_rate = 0.01
        
        for i in range(len(results["ids"][0])):
            memory_id = results["ids"][0][i]
            document = results["documents"][0][i]
            metadata = results["metadatas"][0][i]
            embedding = np.array(results["embeddings"][0][i])
            
            # Calculate raw similarity
            raw_similarity = cosine_similarity(query_embedding, embedding)
            
            # Calculate age and recency weight
            age_days = calculate_age_days(metadata["timestamp"])
            recency_weight = max(0, 1 - decay_rate * age_days) if decay else 1.0
            
            # Calculate final score
            importance = metadata.get("importance", 0.5)
            final_score = raw_similarity * (alpha * recency_weight + (1 - alpha) * importance)
            
            scored_results.append(RecallResult(
                id=memory_id,
                document=document,
                metadata=metadata,
                score=float(final_score),
                raw_similarity=float(raw_similarity),
                age_days=float(age_days)
            ))
        
        # Sort by final score and return top k
        scored_results.sort(key=lambda x: x.score, reverse=True)
        return scored_results[:k]
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error recalling memories: {str(e)}")


@router.get("/collections", response_model=List[CollectionInfo])
async def list_collections():
    """List all ChromaDB collections.
    
    Returns:
        List of collection metadata
    """
    init_services()
    
    try:
        collections = chroma_service.list_collections()
        return [
            CollectionInfo(
                name=col["name"],
                count=col["count"],
                metadata=col["metadata"]
            )
            for col in collections
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing collections: {str(e)}")


@router.get("/collection/{name}/sample")
async def get_collection_sample(
    name: str,
    n: int = Query(20, ge=1, le=100, description="Number of samples")
):
    """Get sample documents from a collection.
    
    Args:
        name: Collection name
        n: Number of samples
        
    Returns:
        Sample documents with metadata and embedding previews
    """
    init_services()
    
    try:
        sample = chroma_service.get_collection_sample(name, n)
        return sample
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Collection not found: {str(e)}")


@router.post("/compact", response_model=CompactionStats)
async def compact():
    """Manually trigger memory compaction.
    
    Returns:
        Compaction statistics
    """
    init_services()
    
    try:
        stats = compaction_service.run_compaction()
        return CompactionStats(**stats)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during compaction: {str(e)}")


@router.get("/stats", response_model=StatsResponse)
async def get_stats():
    """Get system statistics.
    
    Returns:
        Overall system stats
    """
    init_services()
    
    try:
        # Get all memories
        all_data = chroma_service.get_all_memories()
        total_memories = len(all_data["ids"])
        
        # Calculate average age
        if total_memories > 0:
            ages = [calculate_age_days(meta["timestamp"]) for meta in all_data["metadatas"]]
            average_age = sum(ages) / len(ages)
        else:
            average_age = 0.0
        
        # Count topics
        topics = {}
        for meta in all_data["metadatas"]:
            topic = meta.get("topic", "untagged")
            topics[topic] = topics.get(topic, 0) + 1
        
        # Get merge history
        total_merges = merge_logger.get_total_merges()
        merge_log = merge_logger.read_log()
        last_compaction = merge_log[-1]["timestamp"] if merge_log else None
        
        return StatsResponse(
            total_memories=total_memories,
            total_merges=total_merges,
            average_age_days=float(average_age),
            topics=topics,
            last_compaction=last_compaction
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting stats: {str(e)}")


@router.get("/dashboard/umap")
async def get_umap_projection(
    n: int = Query(500, ge=10, le=2000, description="Max points to project")
):
    """Get UMAP 2D projection of embeddings for visualization.
    
    Args:
        n: Maximum number of points to include
        
    Returns:
        2D coordinates and metadata for plotting
    """
    init_services()
    
    try:
        # Get memories
        all_data = chroma_service.get_all_memories(limit=n)
        
        if not all_data["ids"] or len(all_data["ids"]) < 2:
            return {"points": [], "message": "Not enough data for projection"}
        
        embeddings = np.array(all_data["embeddings"])
        
        # Determine projection method based on data size
        if len(embeddings) < 10:
            # Too few points for UMAP, use PCA
            reducer = PCA(n_components=2, random_state=42)
            coords_2d = reducer.fit_transform(embeddings)
        else:
            # Use UMAP for better clustering visualization
            reducer = umap.UMAP(
                n_components=2,
                n_neighbors=min(15, len(embeddings) - 1),
                min_dist=0.1,
                metric='cosine',
                random_state=42
            )
            coords_2d = reducer.fit_transform(embeddings)
        
        # Prepare response
        points = []
        for i, (x, y) in enumerate(coords_2d):
            points.append({
                "id": all_data["ids"][i],
                "x": float(x),
                "y": float(y),
                "document": all_data["documents"][i][:200],  # Truncate for performance
                "metadata": all_data["metadatas"][i],
                "age_days": calculate_age_days(all_data["metadatas"][i]["timestamp"])
            })
        
        return {
            "points": points,
            "projection_method": "UMAP" if len(embeddings) >= 10 else "PCA",
            "total_points": len(points)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating projection: {str(e)}")


@router.get("/dashboard/compaction-log")
async def get_compaction_log(
    limit: int = Query(50, ge=1, le=200, description="Max events to return")
):
    """Get compaction merge history.
    
    Args:
        limit: Maximum number of events
        
    Returns:
        List of merge events
    """
    try:
        events = merge_logger.read_log()
        return {"events": events[-limit:], "total_events": len(events)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading log: {str(e)}")
