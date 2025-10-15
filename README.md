# TraceMind: Autonomous Cognitive Vector Memory System

<div align="center">

![TraceMind](https://img.shields.io/badge/TraceMind-Cognitive%20Memory-00d4ff?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-18-61DAFB?style=flat-square&logo=react&logoColor=black)
![ChromaDB](https://img.shields.io/badge/ChromaDB-Vector%20DB-FF6B6B?style=flat-square)

**Store, recall, and optimize textual memories using vector embeddings with autonomous compaction**

</div>

---

## 🎯 Overview

TraceMind is a **production-lean prototype** of an autonomous cognitive vector memory system that:

- 📝 **Stores** short textual memories as 384-dimensional vectors using `sentence-transformers/all-MiniLM-L6-v2`
- 🔍 **Recalls** memories with semantic search + temporal decay weighting
- 🗜️ **Compacts** redundant memories by clustering and merging similar vectors (cosine similarity ≥ 0.92)
- 📊 **Visualizes** ChromaDB state with UMAP/PCA projections and cluster analysis
- ⏰ **Automates** periodic compaction with APScheduler

The system is designed to demonstrate **reproducible results** with clear before/after compaction states visible in the dashboard.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend (Vite + React)                  │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────────────┐ │
│  │   Remember   │  │    Recall    │  │   Dashboard (UMAP)     │ │
│  └──────────────┘  └──────────────┘  └────────────────────────┘ │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTP/JSON
┌────────────────────────────▼────────────────────────────────────┐
│                     FastAPI Backend (Python)                     │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  API Routes: /remember /recall /compact /stats /umap    │   │
│  └────────┬─────────────────────────────────────────────────┘   │
│           │                                                       │
│  ┌────────▼────────┐  ┌─────────────┐  ┌──────────────────┐    │
│  │  Embeddings     │  │  Compaction │  │   ChromaDB       │    │
│  │  (all-MiniLM)   │  │   Service   │  │   Client         │    │
│  └─────────────────┘  └──────┬──────┘  └────────┬─────────┘    │
│                              │                    │               │
│                       ┌──────▼────────────────────▼──────┐       │
│                       │   APScheduler (30min cycle)      │       │
│                       └──────────────────────────────────┘       │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                    ┌──────────▼───────────┐
                    │  ChromaDB (DuckDB)   │
                    │  Persistent Storage  │
                    │  ./chroma_db/        │
                    └──────────────────────┘
```

---

## 🚀 Quick Start (5 minutes to demo)

### Prerequisites

- **Python 3.10+**
- **Node.js 18+**
- **Git**

### Option 1: Local Development (Recommended)

#### 1. Clone the repository

```bash
git clone <repo-url>
cd TraceMind
```

#### 2. Backend Setup

```bash
cd backend
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

Backend runs at **http://localhost:8000**

#### 3. Frontend Setup (new terminal)

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at **http://localhost:3000**

#### 4. Run Demo Script (new terminal)

```bash
cd scripts
python populate_demo.py
```

This populates 20 example memories, runs compaction, and shows before/after stats.

#### 5. Open Browser

Navigate to **http://localhost:3000** and explore:
- 📝 **Remember**: Add new memories
- 🔍 **Recall**: Query with semantic search
- 📊 **Dashboard**: Visualize clusters and compaction logs

---

### Option 2: Docker Compose

```bash
docker-compose up --build
```

Access at:
- Frontend: http://localhost:3000
- Backend: http://localhost:8000
- API Docs: http://localhost:8000/docs

---

## 📚 API Endpoints

### Core Endpoints

#### `POST /api/remember`
Store a new memory.

```bash
curl -X POST http://localhost:8000/api/remember \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Neural networks are computational models inspired by the brain",
    "topic": "ML",
    "importance": 0.9
  }'
```

**Response:**
```json
{
  "id": "a1b2c3d4-...",
  "status": "stored",
  "timestamp": "2025-10-15T10:30:00Z"
}
```

---

#### `GET /api/recall`
Recall memories with semantic search.

```bash
curl "http://localhost:8000/api/recall?q=machine+learning&k=5&decay=true"
```

**Query Parameters:**
- `q` (required): Query text
- `k` (optional): Number of results (default: 5)
- `decay` (optional): Apply temporal decay (default: true)
- `topic` (optional): Filter by topic

**Response:**
```json
[
  {
    "id": "...",
    "document": "Neural networks are...",
    "metadata": {
      "timestamp": "2025-10-15T10:30:00Z",
      "importance": 0.9,
      "topic": "ML",
      "merge_count": 0
    },
    "score": 0.876,
    "raw_similarity": 0.923,
    "age_days": 0.5
  }
]
```

**Scoring Formula:**
```python
recency_weight = max(0, 1 - 0.01 * age_days)
final_score = cosine_similarity * (0.7 * recency_weight + 0.3 * importance)
```

---

#### `POST /api/compact`
Manually trigger compaction.

```bash
curl -X POST http://localhost:8000/api/compact
```

**Response:**
```json
{
  "before_count": 20,
  "after_count": 15,
  "clusters_merged": 3,
  "items_deleted": 2,
  "merge_events": [
    {
      "timestamp": "2025-10-15T10:35:00Z",
      "cluster_size": 3,
      "merged_ids": ["id1", "id2", "id3"],
      "new_id": "merged_id",
      "representative_text": "Neural networks are..."
    }
  ]
}
```

---

#### `GET /api/stats`
Get system statistics.

```bash
curl http://localhost:8000/api/stats
```

**Response:**
```json
{
  "total_memories": 15,
  "total_merges": 5,
  "average_age_days": 2.3,
  "topics": {
    "ML": 8,
    "cooking": 4,
    "travel": 3
  },
  "last_compaction": "2025-10-15T10:35:00Z"
}
```

---

### ChromaDB Inspection Endpoints

#### `GET /api/collections`
List all ChromaDB collections.

```bash
curl http://localhost:8000/api/collections
```

---

#### `GET /api/collection/{name}/sample?n=20`
Get sample documents from a collection.

```bash
curl "http://localhost:8000/api/collection/memories/sample?n=10"
```

**Response includes:**
- Document texts
- Metadata
- Embedding previews (first 8 dimensions)
- Total embedding dimension

---

### Dashboard Endpoints

#### `GET /api/dashboard/umap?n=500`
Get UMAP/PCA 2D projection of embeddings.

```bash
curl "http://localhost:8000/api/dashboard/umap?n=500"
```

**Response:**
```json
{
  "points": [
    {
      "id": "...",
      "x": -2.34,
      "y": 1.67,
      "document": "Neural networks...",
      "metadata": {...},
      "age_days": 1.2
    }
  ],
  "projection_method": "UMAP",
  "total_points": 500
}
```

---

#### `GET /api/dashboard/compaction-log?limit=50`
Get compaction history.

```bash
curl "http://localhost:8000/api/dashboard/compaction-log?limit=50"
```

---

## 🧠 Compaction Algorithm

### Parameters

```python
SIM_THRESHOLD = 0.92              # Cosine similarity threshold for clustering
MIN_IMPORTANCE_KEEP = 0.2         # Delete threshold for low-importance memories
MAX_CLUSTER_SIZE = 10             # Maximum memories per cluster
DECAY_RATE = 0.01                 # Decay per day (0.01 = 1% per day)
DELETE_AGE_THRESHOLD = 30 days    # Age threshold for deletion eligibility
DELETE_SIMILARITY_THRESHOLD = 0.88 # Similarity for redundancy check
```

### Process

1. **Fetch All Memories**: Retrieve embeddings and metadata from ChromaDB
2. **Build Clusters**: Single-linkage clustering with cosine similarity ≥ 0.92
3. **Merge Clusters**:
   - Compute weighted average embedding:
     ```python
     weight_i = importance_i * max(0, 1 - 0.01 * age_days_i)
     merged_embedding = Σ(weight_i * embedding_i) / Σ(weight_i)
     ```
   - Choose newest document as representative text
   - Aggregate metadata: `merge_count`, `importance = max(...)`, `timestamp = newest`
   - Insert merged memory, delete originals
4. **Delete Redundant**: Low-importance (< 0.2), old (> 30d), with similar survivor (≥ 0.88)
5. **Log Events**: Append to `merge_log.json`

### Example

**Before Compaction:**
```
Memory A: "Neural networks are machine learning models" (similarity: 0.95)
Memory B: "Neural networks represent ML algorithms"
Memory C: "Deep learning neural nets are powerful"
```

**After Compaction:**
```
Merged: "Neural networks are machine learning models"
  - merge_count: 2
  - importance: max(A, B, C)
  - timestamp: newest of (A, B, C)
```

---

## 📊 ChromaDB Schema

### Collection: `memories`

```json
{
  "id": "uuid-string",
  "embedding": [0.12, -0.34, ...],  // 384-dim vector
  "document": "Original text content",
  "metadata": {
    "timestamp": "2025-10-15T10:30:00Z",  // ISO8601 UTC
    "importance": 0.8,                     // 0.0-1.0
    "topic": "ML",                         // Optional tag
    "source": "manual",                    // web/voice/manual
    "last_merged_at": null,                // ISO8601 or null
    "merge_count": 0                       // Increments on merge
  }
}
```

---

## 🧪 Testing

### Run Unit Tests

```bash
cd backend
pytest tests/test_endpoints.py -v
```

### Test Coverage

- ✅ Memory storage and retrieval
- ✅ Recall with decay and topic filters
- ✅ Compaction reduces count on duplicates
- ✅ ChromaDB collection inspection
- ✅ Statistics aggregation
- ✅ UMAP projection generation

### Manual Testing with cURL

```bash
# 1. Add memory
curl -X POST http://localhost:8000/api/remember \
  -H "Content-Type: application/json" \
  -d '{"text": "Test memory", "topic": "test", "importance": 0.5}'

# 2. Recall
curl "http://localhost:8000/api/recall?q=test&k=5"

# 3. Compact
curl -X POST http://localhost:8000/api/compact

# 4. Stats
curl http://localhost:8000/api/stats
```

---

## 🎨 Frontend Features

### Remember Page
- Multi-line text input
- Topic tagging (optional)
- Importance slider (0.0 - 1.0)
- Success confirmation with Dashboard link

### Recall Page
- Semantic search query
- Results slider (k = 1-50)
- Temporal decay toggle
- Topic filter
- Results show:
  - Final score (with decay)
  - Raw cosine similarity
  - Age label (e.g., "2d ago")
  - Importance badge
  - Merge count indicator
- **Rehearsal button**: Re-store memory to boost recency

### Dashboard
- **Stats Cards**: Total memories, merges, average age, topic count
- **ChromaDB Collections**: Live collection metadata
- **Topics Distribution**: Bar chart of memories per topic
- **UMAP/PCA Visualization**:
  - 2D scatter plot of embeddings
  - Color-coded by topic
  - Point size = importance
  - Hover: show document preview
  - Click: full memory details
- **Compaction Log**: Timeline of merge events

---

## 🔧 Configuration

### Backend (`backend/app/services/compaction.py`)

```python
# Adjust compaction parameters
SIM_THRESHOLD = 0.92              # Increase for stricter merging
DECAY_RATE = 0.01                 # Increase for faster decay
```

### Scheduler (`backend/app/main.py`)

```python
# Change compaction frequency
scheduler.add_job(
    scheduled_compaction,
    'interval',
    minutes=30  # Run every 30 minutes
)
```

### Frontend (`frontend/vite.config.js`)

```javascript
proxy: {
  '/api': {
    target: 'http://localhost:8000'  // Backend URL
  }
}
```

---

## 📁 Project Structure

```
TraceMind/
├─ backend/
│  ├─ app/
│  │  ├─ main.py                 # FastAPI app + scheduler
│  │  ├─ models.py               # Pydantic schemas
│  │  ├─ utils.py                # Utilities + MergeLogger
│  │  ├─ api/
│  │  │  └─ routes.py            # API endpoints
│  │  └─ services/
│  │     ├─ embeddings.py        # Sentence-transformers
│  │     ├─ chroma_client.py     # ChromaDB wrapper
│  │     └─ compaction.py        # Compaction algorithm
│  ├─ tests/
│  │  └─ test_endpoints.py       # Pytest tests
│  ├─ requirements.txt
│  └─ Dockerfile
├─ frontend/
│  ├─ src/
│  │  ├─ App.jsx                 # Main router
│  │  ├─ main.jsx                # Entry point
│  │  └─ pages/
│  │     ├─ Remember.jsx         # Memory creation
│  │     ├─ Recall.jsx           # Search interface
│  │     └─ Dashboard.jsx        # Visualization
│  ├─ package.json
│  ├─ vite.config.js
│  ├─ tailwind.config.js
│  └─ Dockerfile
├─ scripts/
│  └─ populate_demo.py           # Demo data populator
├─ docker-compose.yml
└─ README.md
```

---

## 🎯 Acceptance Criteria (Verification)

### ✅ Criterion 1: Compaction Reduces Count

```bash
# Add 10 similar memories
for i in {1..10}; do
  curl -X POST http://localhost:8000/api/remember \
    -H "Content-Type: application/json" \
    -d "{\"text\": \"Neural networks are ML model $i\", \"importance\": 0.7}"
done

# Check before
curl http://localhost:8000/api/stats | jq .total_memories

# Compact
curl -X POST http://localhost:8000/api/compact | jq

# Check after (should be < 10)
curl http://localhost:8000/api/stats | jq .total_memories
```

**Expected**: Memory count decreases, merge events created.

---

### ✅ Criterion 2: Recall with Temporal Weighting

```bash
curl "http://localhost:8000/api/recall?q=neural+network&k=5&decay=true" | jq
```

**Expected**: Results show `score` < `raw_similarity` for older memories due to decay.

---

### ✅ Criterion 3: Dashboard UMAP Shows Clusters

1. Visit http://localhost:3000/dashboard
2. Observe 2D scatter plot with color-coded topics
3. Click a point → see metadata popup

**Expected**: Clear clustering by topic, hover works, merge counts visible.

---

### ✅ Criterion 4: ChromaDB Inspection

```bash
curl "http://localhost:8000/api/collection/memories/sample?n=10" | jq
```

**Expected**: Returns documents, metadatas, embedding previews (8 dims), total dimension.

---

### ✅ Criterion 5: Demo Script

```bash
cd scripts
python populate_demo.py
```

**Expected**: Prints before/after counts, merge events, recall results clearly.

---

## 🚧 Known Limitations & Future Work

### Current Limitations
- Single collection (`memories`) — no multi-user support
- In-memory clustering (O(n²)) — not optimized for > 10k memories
- No authentication/authorization
- Scheduler runs in-process (not distributed)

### Future Enhancements
- **User isolation**: Per-user collections (`user_<id>_memories`)
- **Incremental compaction**: Window-based processing for scale
- **LLM summarization**: Generate human-readable summaries for merged clusters
- **Approximate nearest neighbors**: Use FAISS/Annoy for > 100k vectors
- **Redis + Celery**: Distributed task queue for compaction
- **Chunk long documents**: Split > 512 tokens into sub-memories with `chunk_index`

---

## 📖 API Documentation

Interactive API docs available at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is provided as-is for educational and demonstration purposes.

---

## 🙏 Acknowledgments

- **sentence-transformers** by UKPLab for the all-MiniLM-L6-v2 model
- **ChromaDB** for the embedded vector database
- **FastAPI** for the high-performance web framework
- **UMAP** algorithm by McInnes et al. for dimensionality reduction

---

## 📞 Support

For issues or questions:
1. Check existing GitHub issues
2. Review API documentation at `/docs`
3. Run the demo script to verify setup
4. Open a new issue with reproduction steps

---

**Built with ❤️ for demonstrable, reproducible cognitive memory systems**
