# TraceMind - Quick Start Guide

## Fastest Way to See Results (< 5 minutes)

### Step 1: Install Backend Dependencies
```powershell
cd backend
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

### Step 2: Start Backend
```powershell
python -m uvicorn app.main:app --reload
```
✅ Backend running at http://localhost:8000

### Step 3: Install Frontend Dependencies (new PowerShell window)
```powershell
cd frontend
npm install
```

### Step 4: Start Frontend
```powershell
npm run dev
```
✅ Frontend running at http://localhost:3000

### Step 5: Run Demo (new PowerShell window)
```powershell
cd scripts
python populate_demo.py
```

### Step 6: Open Browser
Navigate to **http://localhost:3000/dashboard**

You should see:
- ✅ 15+ memories visualized in UMAP plot
- ✅ Compaction log showing merge events
- ✅ Topic distribution charts
- ✅ Interactive memory exploration

---

## Quick API Test

```powershell
# Add a memory
curl -X POST http://localhost:8000/api/remember -H "Content-Type: application/json" -d '{\"text\": \"Test memory\", \"importance\": 0.8}'

# Search
curl "http://localhost:8000/api/recall?q=test&k=5"

# Compact
curl -X POST http://localhost:8000/api/compact

# Stats
curl http://localhost:8000/api/stats
```

---

## Troubleshooting

### "Module not found" errors
```powershell
cd backend
pip install -r requirements.txt
```

### "Cannot connect to backend"
Make sure backend is running on port 8000:
```powershell
cd backend
.\venv\Scripts\activate
python -m uvicorn app.main:app --reload
```

### Frontend won't start
```powershell
cd frontend
rm -r node_modules
npm install
npm run dev
```

### ChromaDB errors
Delete and restart:
```powershell
rm -r backend/chroma_db
# Restart backend
```

---

## Architecture Overview

```
┌─────────────────┐
│  React Frontend │  ← http://localhost:3000
│  (Vite + Tailwind)
└────────┬────────┘
         │ /api/*
┌────────▼────────┐
│  FastAPI Backend│  ← http://localhost:8000
│  (Python 3.10+) │
└────────┬────────┘
         │
┌────────▼────────┐
│    ChromaDB     │  ← ./chroma_db/ (persistent)
│  (DuckDB+Parquet)
└─────────────────┘
```

---

## Next Steps

1. **Explore the UI** at http://localhost:3000
   - Remember: Add new memories
   - Recall: Search semantically
   - Dashboard: Visualize clusters

2. **Read the API docs** at http://localhost:8000/docs

3. **Customize compaction** in `backend/app/services/compaction.py`

4. **Add your own memories** via UI or API

---

## Key Files

- `backend/app/main.py` - FastAPI app + scheduler
- `backend/app/services/compaction.py` - Compaction algorithm
- `frontend/src/pages/Dashboard.jsx` - UMAP visualization
- `scripts/populate_demo.py` - Demo data generator

---

**Need help?** Check README.md for full documentation.
