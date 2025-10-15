"""Utility functions for TraceMind."""
import json
import os
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Optional
import numpy as np


def get_utc_now() -> datetime:
    """Get current UTC datetime."""
    return datetime.now(timezone.utc)


def to_iso_string(dt: datetime) -> str:
    """Convert datetime to ISO8601 string."""
    return dt.isoformat()


def from_iso_string(iso_str: str) -> datetime:
    """Parse ISO8601 string to datetime."""
    # Handle both naive and aware timestamps
    try:
        dt = datetime.fromisoformat(iso_str.replace('Z', '+00:00'))
        # If naive, assume UTC
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except ValueError:
        # Fallback for other formats
        dt = datetime.fromisoformat(iso_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt


def calculate_age_days(timestamp_str: str) -> float:
    """Calculate age in days from ISO timestamp."""
    ts = from_iso_string(timestamp_str)
    now = get_utc_now()
    return (now - ts).total_seconds() / 86400.0


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Calculate cosine similarity between two vectors."""
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


class MergeLogger:
    """Logger for compaction merge events."""
    
    def __init__(self, log_file: str = "merge_log.json"):
        self.log_file = log_file
        self._ensure_log_file()
    
    def _ensure_log_file(self):
        """Create log file if it doesn't exist."""
        if not os.path.exists(self.log_file):
            with open(self.log_file, 'w') as f:
                json.dump([], f)
    
    def log_merge(self, event: Dict[str, Any]):
        """Append a merge event to the log."""
        events = self.read_log()
        events.append(event)
        with open(self.log_file, 'w') as f:
            json.dump(events, f, indent=2)
    
    def read_log(self) -> List[Dict[str, Any]]:
        """Read all merge events."""
        try:
            with open(self.log_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []
    
    def get_total_merges(self) -> int:
        """Get total number of merge events."""
        return len(self.read_log())
    
    def clear_log(self):
        """Clear the merge log."""
        with open(self.log_file, 'w') as f:
            json.dump([], f)


def create_metadata(
    importance: float = 0.5,
    topic: Optional[str] = None,
    source: str = "manual"
) -> Dict[str, Any]:
    """Create metadata dict for ChromaDB storage."""
    metadata = {
        "timestamp": to_iso_string(get_utc_now()),
        "importance": float(importance),
        "source": source,
        "merge_count": 0
    }
    if topic:
        metadata["topic"] = topic
    # Note: last_merged_at is only added when memories are merged
    return metadata
