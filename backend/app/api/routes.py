"""API routes for TraceMind."""
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from datetime import datetime, timedelta
import numpy as np
from sklearn.decomposition import PCA
from umap import UMAP

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
    topic: str = Query("", description="Filter by topic (empty string for no filter)")
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
        where_filter = None
        if topic and topic != "":
            where_filter = {"topic": topic}
        
        # Query ChromaDB
        if where_filter is not None:
            results = chroma_service.query_memories(
                query_embedding=query_embedding,
                n_results=k_raw,
                where=where_filter
            )
        else:
            results = chroma_service.query_memories(
                query_embedding=query_embedding,
                n_results=k_raw
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
            reducer = UMAP(
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


@router.post("/demo")
async def run_demo():
    """Run a comprehensive TraceMind lifecycle demo.
    
    Returns:
        Demo results showing full pipeline evolution
    """
    init_services()
    
    try:
        # Phase 1: Initial memories (Day 1)
        phase1_memories = [
            {"text": "Started learning about neural networks today", "topic": "ML", "importance": 0.8},
            {"text": "Deep learning uses multiple layers of neurons", "topic": "ML", "importance": 0.7},
            {"text": "Paris is the capital of France with beautiful architecture", "topic": "travel", "importance": 0.6},
            {"text": "Time blocking helps me stay focused on tasks", "topic": "productivity", "importance": 0.5},
        ]
        
        # Phase 2: More memories (Day 2) 
        phase2_memories = [
            {"text": "Convolutional neural networks excel at image processing", "topic": "ML", "importance": 0.9},
            {"text": "Transfer learning saves training time by reusing models", "topic": "ML", "importance": 0.8},
            {"text": "The Eiffel Tower was built for the 1889 World's Fair", "topic": "travel", "importance": 0.7},
            {"text": "Cherry blossoms in Japan are absolutely stunning", "topic": "travel", "importance": 0.6},
            {"text": "The Pomodoro Technique uses 25-minute work sessions", "topic": "productivity", "importance": 0.6},
            {"text": "Regular exercise improves both mental and physical health", "topic": "health", "importance": 0.7},
        ]
        
        # Phase 3: Recent memories (Day 3)
        phase3_memories = [
            {"text": "Recurrent neural networks handle sequential data well", "topic": "ML", "importance": 0.8},
            {"text": "Machine learning models need good data quality", "topic": "ML", "importance": 0.6},
            {"text": "Tokyo combines traditional temples with modern skyscrapers", "topic": "travel", "importance": 0.8},
            {"text": "Daily meditation reduces stress significantly", "topic": "health", "importance": 0.8},
            {"text": "Sleep is crucial for memory consolidation", "topic": "health", "importance": 0.7},
            {"text": "Carbonara pasta requires eggs, cheese, and cured pork", "topic": "cooking", "importance": 0.4},
        ]
        
        # Clear existing data
        chroma_service.clear_collection()
        merge_logger.clear_log()
        
        demo_phases = []
        
        # Phase 1: Add initial memories
        for memory in phase1_memories:
            embedding = embedding_service.embed_single(memory["text"])
            metadata = create_metadata(
                importance=memory["importance"],
                topic=memory["topic"]
            )
            # Simulate older timestamp (2 days ago)
            metadata["timestamp"] = (datetime.now() - timedelta(days=2)).isoformat()
            chroma_service.add_memory(
                text=memory["text"],
                embedding=embedding,
                metadata=metadata
            )
        
        phase1_stats = await get_stats()
        phase1_umap = await get_umap_projection(n=100)
        
        demo_phases.append({
            "phase": 1,
            "name": "Initial Memories (Day 1)",
            "memories_added": len(phase1_memories),
            "total_memories": phase1_stats.total_memories,
            "topics": list(phase1_stats.topics.keys()),
            "umap_data": phase1_umap
        })
        
        # Phase 2: Add more memories (simulate next day)
        for memory in phase2_memories:
            embedding = embedding_service.embed_single(memory["text"])
            metadata = create_metadata(
                importance=memory["importance"],
                topic=memory["topic"]
            )
            # Simulate yesterday
            metadata["timestamp"] = (datetime.now() - timedelta(days=1)).isoformat()
            chroma_service.add_memory(
                text=memory["text"],
                embedding=embedding,
                metadata=metadata
            )
        
        phase2_stats = await get_stats()
        phase2_umap = await get_umap_projection(n=100)
        
        demo_phases.append({
            "phase": 2,
            "name": "Growing Knowledge (Day 2)",
            "memories_added": len(phase2_memories),
            "total_memories": phase2_stats.total_memories,
            "topics": list(phase2_stats.topics.keys()),
            "umap_data": phase2_umap
        })
        
        # Phase 3: First compaction
        compaction1_stats = compaction_service.run_compaction()
        
        phase3_stats = await get_stats()
        phase3_umap = await get_umap_projection(n=100)
        
        demo_phases.append({
            "phase": 3,
            "name": "First Compaction",
            "compaction_results": compaction1_stats,
            "total_memories": phase3_stats.total_memories,
            "total_merges": phase3_stats.total_merges,
            "umap_data": phase3_umap
        })
        
        # Phase 4: Add recent memories
        for memory in phase3_memories:
            embedding = embedding_service.embed_single(memory["text"])
            metadata = create_metadata(
                importance=memory["importance"],
                topic=memory["topic"]
            )
            # Current timestamp
            chroma_service.add_memory(
                text=memory["text"],
                embedding=embedding,
                metadata=metadata
            )
        
        phase4_stats = await get_stats()
        phase4_umap = await get_umap_projection(n=100)
        
        demo_phases.append({
            "phase": 4,
            "name": "Recent Memories (Day 3)",
            "memories_added": len(phase3_memories),
            "total_memories": phase4_stats.total_memories,
            "topics": list(phase4_stats.topics.keys()),
            "umap_data": phase4_umap
        })
        
        # Phase 5: Second compaction
        compaction2_stats = compaction_service.run_compaction()
        
        phase5_stats = await get_stats()
        phase5_umap = await get_umap_projection(n=100)
        compaction_log = await get_compaction_log(limit=50)
        
        demo_phases.append({
            "phase": 5,
            "name": "Final Compaction & Evolution",
            "compaction_results": compaction2_stats,
            "total_memories": phase5_stats.total_memories,
            "total_merges": phase5_stats.total_merges,
            "umap_data": phase5_umap
        })
        
        # Test recall functionality
        recall_tests = [
            {"query": "neural networks", "expected_topic": "ML"},
            {"query": "travel destinations", "expected_topic": "travel"},
            {"query": "productivity techniques", "expected_topic": "productivity"},
            {"query": "healthy habits", "expected_topic": "health"}
        ]
        
        recall_results = []
        for test in recall_tests:
            # Call recall logic directly instead of the endpoint
            query_embedding = embedding_service.embed_single(test["query"])
            k_raw = min(3 * 2, 100)
            where_filter = None  # No topic filter for demo
            
            results = chroma_service.query_memories(
                query_embedding=query_embedding,
                n_results=k_raw,
                where=where_filter
            )
            
            if results["ids"][0]:
                # Rerank with temporal decay
                scored_results = []
                alpha = 0.7
                decay_rate = 0.01
                
                for i in range(len(results["ids"][0])):
                    memory_id = results["ids"][0][i]
                    document = results["documents"][0][i]
                    metadata = results["metadatas"][0][i]
                    embedding = np.array(results["embeddings"][0][i])
                    
                    raw_similarity = cosine_similarity(query_embedding, embedding)
                    age_days = calculate_age_days(metadata["timestamp"])
                    recency_weight = max(0, 1 - decay_rate * age_days)
                    
                    importance = metadata.get("importance", 0.5)
                    final_score = raw_similarity * (alpha * recency_weight + (1 - alpha) * importance)
                    
                    scored_results.append({
                        "id": memory_id,
                        "document": document,
                        "metadata": metadata,
                        "score": float(final_score),
                        "raw_similarity": float(raw_similarity),
                        "age_days": float(age_days)
                    })
                
                scored_results.sort(key=lambda x: x["score"], reverse=True)
                top_results = scored_results[:3]
            else:
                top_results = []
            
            recall_results.append({
                "query": test["query"],
                "results_count": len(top_results),
                "top_result": top_results[0]["document"][:100] + "..." if top_results else None,
                "expected_topic": test["expected_topic"]
            })
        
        return {
            "success": True,
            "message": "Full TraceMind lifecycle demo completed!",
            "phases": demo_phases,
            "final_stats": phase5_stats,
            "compaction_log": compaction_log,
            "recall_tests": recall_results,
            "lifecycle_summary": {
                "total_memories_added": len(phase1_memories + phase2_memories + phase3_memories),
                "total_compactions": 2,
                "total_merges": phase5_stats.total_merges,
                "topics_covered": list(phase5_stats.topics.keys()),
                "avg_age_days": phase5_stats.average_age_days
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Demo failed: {str(e)}")
