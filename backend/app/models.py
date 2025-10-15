"""Data models for TraceMind."""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class MemoryInput(BaseModel):
    """Input schema for creating a new memory."""
    text: str = Field(..., min_length=1, max_length=10000, description="Memory text content")
    topic: Optional[str] = Field(None, max_length=100, description="Optional topic tag")
    importance: float = Field(0.5, ge=0.0, le=1.0, description="Importance score 0-1")
    source: Optional[str] = Field("manual", description="Source: web/voice/manual")


class MemoryResponse(BaseModel):
    """Response schema for created memory."""
    id: str
    status: str
    timestamp: str


class RecallQuery(BaseModel):
    """Query parameters for recall."""
    q: str = Field(..., min_length=1, description="Query text")
    k: int = Field(5, ge=1, le=50, description="Number of results")
    decay: bool = Field(True, description="Apply temporal decay")
    topic: Optional[str] = Field(None, description="Filter by topic")


class RecallResult(BaseModel):
    """Single recall result."""
    id: str
    document: str
    metadata: dict
    score: float
    raw_similarity: float
    age_days: float


class CollectionInfo(BaseModel):
    """ChromaDB collection metadata."""
    name: str
    count: int
    metadata: Optional[dict]


class CompactionStats(BaseModel):
    """Statistics from compaction run."""
    before_count: int
    after_count: int
    clusters_merged: int
    items_deleted: int
    merge_events: List[dict]
    timestamp: str


class StatsResponse(BaseModel):
    """Overall system statistics."""
    total_memories: int
    total_merges: int
    average_age_days: float
    topics: dict
    last_compaction: Optional[str]
