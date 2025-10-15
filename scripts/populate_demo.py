"""Demo script to populate TraceMind with example memories and demonstrate compaction."""
import requests
import time
import json
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000/api"

# Example memories across different topics
DEMO_MEMORIES = [
    # ML/AI memories
    {"text": "Neural networks are computational models inspired by biological neurons", "topic": "ML", "importance": 0.9},
    {"text": "Deep learning uses multiple layers of neural networks to learn hierarchical representations", "topic": "ML", "importance": 0.9},
    {"text": "Convolutional neural networks are specialized for processing grid-like data such as images", "topic": "ML", "importance": 0.8},
    {"text": "Transfer learning allows models to leverage knowledge from related tasks", "topic": "ML", "importance": 0.7},
    {"text": "Backpropagation is the algorithm used to train neural networks", "topic": "ML", "importance": 0.8},
    {"text": "Neural networks consist of interconnected layers that process information", "topic": "ML", "importance": 0.85},
    
    # Cooking memories
    {"text": "To make pasta carbonara, mix eggs, parmesan, and pasta with crispy pancetta", "topic": "cooking", "importance": 0.6},
    {"text": "The secret to fluffy pancakes is not overmixing the batter", "topic": "cooking", "importance": 0.5},
    {"text": "Pasta carbonara is made with eggs, cheese, pasta, and cured pork", "topic": "cooking", "importance": 0.6},
    {"text": "Always salt pasta water generously before adding pasta", "topic": "cooking", "importance": 0.4},
    
    # Travel memories
    {"text": "Paris has beautiful architecture including the Eiffel Tower and Notre-Dame", "topic": "travel", "importance": 0.7},
    {"text": "The best time to visit Japan is during cherry blossom season in spring", "topic": "travel", "importance": 0.6},
    {"text": "Tokyo combines traditional temples with modern skyscrapers", "topic": "travel", "importance": 0.6},
    {"text": "Iceland is known for its stunning natural landscapes and northern lights", "topic": "travel", "importance": 0.7},
    
    # Work/productivity memories
    {"text": "Time blocking helps improve focus by dedicating specific time slots to tasks", "topic": "productivity", "importance": 0.7},
    {"text": "The Pomodoro Technique uses 25-minute focused work intervals", "topic": "productivity", "importance": 0.6},
    {"text": "Regular breaks during work improve overall productivity and creativity", "topic": "productivity", "importance": 0.5},
    
    # Personal memories
    {"text": "Daily exercise improves both physical and mental health", "topic": "health", "importance": 0.8},
    {"text": "Meditation can reduce stress and improve focus", "topic": "health", "importance": 0.7},
    {"text": "Getting 7-8 hours of sleep is crucial for cognitive function", "topic": "health", "importance": 0.9},
]


def print_section(title):
    """Print a section header."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)


def add_memory(text, topic, importance):
    """Add a memory to TraceMind."""
    response = requests.post(
        f"{BASE_URL}/remember",
        json={"text": text, "topic": topic, "importance": importance}
    )
    return response.json()


def get_stats():
    """Get system statistics."""
    response = requests.get(f"{BASE_URL}/stats")
    return response.json()


def run_compaction():
    """Run compaction."""
    response = requests.post(f"{BASE_URL}/compact")
    return response.json()


def recall_memories(query, k=5):
    """Recall memories."""
    response = requests.get(
        f"{BASE_URL}/recall",
        params={"q": query, "k": k, "decay": True}
    )
    return response.json()


def main():
    """Run the demo."""
    print_section("TraceMind Demo Script")
    print("This script demonstrates TraceMind's memory storage and compaction capabilities.\n")
    
    # Step 1: Populate memories
    print_section("STEP 1: Populating Memories")
    print(f"Adding {len(DEMO_MEMORIES)} memories across different topics...\n")
    
    for i, memory in enumerate(DEMO_MEMORIES, 1):
        result = add_memory(memory["text"], memory["topic"], memory["importance"])
        print(f"  [{i}/{len(DEMO_MEMORIES)}] Added: {memory['text'][:60]}... (ID: {result['id'][:8]})")
        time.sleep(0.1)  # Small delay for visibility
    
    # Step 2: Check stats before compaction
    print_section("STEP 2: Statistics Before Compaction")
    stats_before = get_stats()
    print(f"  Total Memories: {stats_before['total_memories']}")
    print(f"  Average Age: {stats_before['average_age_days']:.2f} days")
    print(f"  Total Merges: {stats_before['total_merges']}")
    print(f"\n  Topics Distribution:")
    for topic, count in sorted(stats_before['topics'].items()):
        print(f"    - {topic}: {count}")
    
    # Step 3: Test recall
    print_section("STEP 3: Testing Recall")
    test_queries = [
        "machine learning neural networks",
        "cooking pasta dishes",
        "travel destinations"
    ]
    
    for query in test_queries:
        print(f"\n  Query: '{query}'")
        results = recall_memories(query, k=3)
        for i, result in enumerate(results[:3], 1):
            print(f"    {i}. [Score: {result['score']:.3f}] {result['document'][:70]}...")
    
    # Step 4: Run compaction
    print_section("STEP 4: Running Compaction")
    print("  Compacting similar memories...\n")
    compaction_result = run_compaction()
    
    print(f"  Before: {compaction_result['before_count']} memories")
    print(f"  After: {compaction_result['after_count']} memories")
    print(f"  Clusters Merged: {compaction_result['clusters_merged']}")
    print(f"  Items Deleted: {compaction_result['items_deleted']}")
    
    if compaction_result['merge_events']:
        print(f"\n  Merge Events:")
        for event in compaction_result['merge_events']:
            print(f"    - Merged {event['cluster_size']} memories into one")
            print(f"      Representative: {event['representative_text'][:60]}...")
    
    # Step 5: Stats after compaction
    print_section("STEP 5: Statistics After Compaction")
    stats_after = get_stats()
    print(f"  Total Memories: {stats_after['total_memories']}")
    print(f"  Total Merges: {stats_after['total_merges']}")
    print(f"  Reduction: {stats_before['total_memories'] - stats_after['total_memories']} memories")
    
    # Step 6: Test recall after compaction
    print_section("STEP 6: Recall After Compaction")
    query = "neural networks and deep learning"
    print(f"  Query: '{query}'\n")
    results = recall_memories(query, k=5)
    
    for i, result in enumerate(results, 1):
        merge_info = f" [Merged {result['metadata']['merge_count']}x]" if result['metadata'].get('merge_count', 0) > 0 else ""
        print(f"    {i}. [Score: {result['score']:.3f}]{merge_info}")
        print(f"       {result['document'][:80]}...")
    
    # Summary
    print_section("SUMMARY")
    print("  ✓ Successfully populated TraceMind with example memories")
    print("  ✓ Demonstrated semantic recall with temporal weighting")
    print("  ✓ Compaction merged similar memories to reduce redundancy")
    print(f"  ✓ ChromaDB now contains {stats_after['total_memories']} optimized memories")
    print("\n  🎯 Next steps:")
    print("     - Open http://localhost:3000 to explore the web interface")
    print("     - Visit the Dashboard to see UMAP visualization")
    print("     - Try adding your own memories and queries")
    print("\n")


if __name__ == "__main__":
    try:
        main()
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Cannot connect to TraceMind backend.")
        print("   Make sure the backend is running on http://localhost:8000")
        print("   Run: cd backend && python -m uvicorn app.main:app --reload")
    except Exception as e:
        print(f"\n❌ Error: {e}")
