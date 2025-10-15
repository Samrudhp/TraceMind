"""Unit tests for TraceMind API endpoints."""
import pytest
from fastapi.testclient import TestClient
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.main import app
from app.services.chroma_client import get_chroma_service

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_and_teardown():
    """Setup and teardown for each test."""
    # Setup: clear the collection before each test
    chroma = get_chroma_service()
    chroma.clear_collection()
    yield
    # Teardown (optional)


def test_root_endpoint():
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "TraceMind"
    assert "version" in data


def test_health_endpoint():
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_remember_memory():
    """Test storing a new memory."""
    payload = {
        "text": "Machine learning is a subset of artificial intelligence",
        "topic": "ML",
        "importance": 0.8
    }
    
    response = client.post("/api/remember", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    assert "id" in data
    assert data["status"] == "stored"
    assert "timestamp" in data


def test_remember_minimal():
    """Test storing memory with minimal data."""
    payload = {
        "text": "This is a simple memory"
    }
    
    response = client.post("/api/remember", json=payload)
    assert response.status_code == 200
    assert response.json()["status"] == "stored"


def test_remember_invalid():
    """Test storing invalid memory."""
    payload = {
        "text": "",  # Empty text should fail
    }
    
    response = client.post("/api/remember", json=payload)
    assert response.status_code == 422  # Validation error


def test_recall_memories():
    """Test recalling memories."""
    # First, store some memories
    memories = [
        {"text": "Neural networks are powerful", "topic": "ML", "importance": 0.9},
        {"text": "Deep learning uses multiple layers", "topic": "ML", "importance": 0.8},
        {"text": "Pizza is delicious", "topic": "food", "importance": 0.5}
    ]
    
    for mem in memories:
        client.post("/api/remember", json=mem)
    
    # Recall with query
    response = client.get("/api/recall", params={"q": "artificial intelligence", "k": 5})
    assert response.status_code == 200
    
    results = response.json()
    assert isinstance(results, list)
    assert len(results) <= 5
    
    # Check result structure
    if results:
        result = results[0]
        assert "id" in result
        assert "document" in result
        assert "score" in result
        assert "raw_similarity" in result
        assert "age_days" in result
        assert "metadata" in result


def test_recall_with_topic_filter():
    """Test recall with topic filter."""
    # Store memories
    client.post("/api/remember", json={"text": "ML concept", "topic": "ML"})
    client.post("/api/remember", json={"text": "Cooking recipe", "topic": "cooking"})
    
    # Recall with topic filter
    response = client.get("/api/recall", params={"q": "concept", "k": 5, "topic": "ML"})
    assert response.status_code == 200
    
    results = response.json()
    # Should only return ML memories
    for result in results:
        assert result["metadata"].get("topic") == "ML"


def test_list_collections():
    """Test listing ChromaDB collections."""
    response = client.get("/api/collections")
    assert response.status_code == 200
    
    collections = response.json()
    assert isinstance(collections, list)
    assert len(collections) > 0
    
    # Check structure
    col = collections[0]
    assert "name" in col
    assert "count" in col


def test_get_collection_sample():
    """Test getting collection sample."""
    # Store a memory first
    client.post("/api/remember", json={"text": "Test memory"})
    
    response = client.get("/api/collection/memories/sample?n=10")
    assert response.status_code == 200
    
    data = response.json()
    assert "ids" in data
    assert "documents" in data
    assert "metadatas" in data


def test_compaction():
    """Test compaction reduces memory count when duplicates exist."""
    # Store similar memories
    similar_texts = [
        "Neural networks are a type of machine learning",
        "Neural networks represent machine learning models",
        "Machine learning neural networks are powerful"
    ]
    
    for text in similar_texts:
        client.post("/api/remember", json={"text": text, "importance": 0.7})
    
    # Get count before
    stats_before = client.get("/api/stats").json()
    count_before = stats_before["total_memories"]
    
    # Run compaction
    response = client.post("/api/compact")
    assert response.status_code == 200
    
    data = response.json()
    assert "before_count" in data
    assert "after_count" in data
    assert "clusters_merged" in data
    
    # Count should decrease if similar memories were merged
    # (might not always happen depending on threshold)
    assert data["after_count"] <= data["before_count"]


def test_get_stats():
    """Test getting system statistics."""
    # Store some memories
    client.post("/api/remember", json={"text": "Memory 1", "topic": "test"})
    client.post("/api/remember", json={"text": "Memory 2", "topic": "test"})
    
    response = client.get("/api/stats")
    assert response.status_code == 200
    
    stats = response.json()
    assert "total_memories" in stats
    assert "total_merges" in stats
    assert "average_age_days" in stats
    assert "topics" in stats
    assert stats["total_memories"] >= 2


def test_umap_projection():
    """Test UMAP projection endpoint."""
    # Store enough memories for projection
    for i in range(5):
        client.post("/api/remember", json={"text": f"Memory number {i}"})
    
    response = client.get("/api/dashboard/umap?n=100")
    assert response.status_code == 200
    
    data = response.json()
    assert "points" in data
    
    if data["points"]:
        point = data["points"][0]
        assert "x" in point
        assert "y" in point
        assert "id" in point
        assert "document" in point


def test_compaction_log():
    """Test compaction log endpoint."""
    response = client.get("/api/dashboard/compaction-log?limit=10")
    assert response.status_code == 200
    
    data = response.json()
    assert "events" in data
    assert "total_events" in data
    assert isinstance(data["events"], list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
