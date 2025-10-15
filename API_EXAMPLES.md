# TraceMind - API Examples

## cURL Examples

### 1. Health Check
```bash
curl http://localhost:8000/health
```

### 2. Store Memories

#### Simple Memory
```bash
curl -X POST http://localhost:8000/api/remember \
  -H "Content-Type: application/json" \
  -d '{"text": "Python is a high-level programming language"}'
```

#### Memory with Metadata
```bash
curl -X POST http://localhost:8000/api/remember \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Neural networks are inspired by biological neurons in the brain",
    "topic": "ML",
    "importance": 0.9
  }'
```

#### Batch Insert (PowerShell)
```powershell
$memories = @(
  @{text="Deep learning uses multiple layers"; topic="ML"; importance=0.8},
  @{text="Pasta carbonara uses eggs and cheese"; topic="cooking"; importance=0.6},
  @{text="Paris is known for the Eiffel Tower"; topic="travel"; importance=0.7}
)

foreach ($mem in $memories) {
  $json = $mem | ConvertTo-Json
  curl.exe -X POST http://localhost:8000/api/remember `
    -H "Content-Type: application/json" `
    -d $json
  Start-Sleep -Milliseconds 100
}
```

### 3. Recall Memories

#### Basic Query
```bash
curl "http://localhost:8000/api/recall?q=machine+learning&k=5"
```

#### With All Parameters
```bash
curl "http://localhost:8000/api/recall?q=neural+networks&k=10&decay=true&topic=ML"
```

#### No Decay
```bash
curl "http://localhost:8000/api/recall?q=cooking&k=5&decay=false"
```

### 4. Compaction

#### Trigger Compaction
```bash
curl -X POST http://localhost:8000/api/compact
```

#### Check Compaction Log
```bash
curl "http://localhost:8000/api/dashboard/compaction-log?limit=10"
```

### 5. Statistics

#### Overall Stats
```bash
curl http://localhost:8000/api/stats
```

#### Collections
```bash
curl http://localhost:8000/api/collections
```

#### Collection Sample
```bash
curl "http://localhost:8000/api/collection/memories/sample?n=20"
```

### 6. Visualization

#### UMAP Projection
```bash
curl "http://localhost:8000/api/dashboard/umap?n=500"
```

---

## Python Examples

### Using requests library

```python
import requests
import json

BASE_URL = "http://localhost:8000/api"

# 1. Add memory
response = requests.post(
    f"{BASE_URL}/remember",
    json={
        "text": "Transformers revolutionized NLP",
        "topic": "ML",
        "importance": 0.95
    }
)
print(f"Memory ID: {response.json()['id']}")

# 2. Search
response = requests.get(
    f"{BASE_URL}/recall",
    params={
        "q": "natural language processing",
        "k": 5,
        "decay": True
    }
)
for i, result in enumerate(response.json(), 1):
    print(f"{i}. [{result['score']:.3f}] {result['document'][:60]}...")

# 3. Get stats
response = requests.get(f"{BASE_URL}/stats")
stats = response.json()
print(f"Total memories: {stats['total_memories']}")
print(f"Topics: {list(stats['topics'].keys())}")

# 4. Compact
response = requests.post(f"{BASE_URL}/compact")
compaction = response.json()
print(f"Compacted: {compaction['before_count']} → {compaction['after_count']}")
```

---

## JavaScript/Axios Examples

### For Frontend Integration

```javascript
import axios from 'axios';

const API_BASE = '/api';

// 1. Remember
const addMemory = async (text, topic, importance) => {
  const response = await axios.post(`${API_BASE}/remember`, {
    text,
    topic,
    importance
  });
  return response.data;
};

// 2. Recall
const searchMemories = async (query, k = 5, decay = true) => {
  const response = await axios.get(`${API_BASE}/recall`, {
    params: { q: query, k, decay }
  });
  return response.data;
};

// 3. Get Stats
const getStats = async () => {
  const response = await axios.get(`${API_BASE}/stats`);
  return response.data;
};

// 4. Compact
const runCompaction = async () => {
  const response = await axios.post(`${API_BASE}/compact`);
  return response.data;
};

// 5. Get UMAP Data
const getUmapData = async (n = 500) => {
  const response = await axios.get(`${API_BASE}/dashboard/umap`, {
    params: { n }
  });
  return response.data;
};

// Usage
(async () => {
  // Add memory
  const memory = await addMemory(
    "React is a JavaScript library for UIs",
    "programming",
    0.8
  );
  console.log('Added:', memory.id);

  // Search
  const results = await searchMemories("JavaScript", 5, true);
  console.log('Found:', results.length, 'memories');

  // Stats
  const stats = await getStats();
  console.log('Total:', stats.total_memories);
})();
```

---

## Testing Workflow

### Complete End-to-End Test

```bash
#!/bin/bash

echo "=== TraceMind API Test ==="

# 1. Check health
echo -e "\n1. Health check..."
curl -s http://localhost:8000/health | jq

# 2. Add memories
echo -e "\n2. Adding memories..."
for i in {1..5}; do
  curl -s -X POST http://localhost:8000/api/remember \
    -H "Content-Type: application/json" \
    -d "{\"text\": \"Memory $i about neural networks\", \"importance\": 0.7}" \
    | jq -r '.id'
done

# 3. Get stats before
echo -e "\n3. Stats before compaction..."
BEFORE=$(curl -s http://localhost:8000/api/stats | jq -r '.total_memories')
echo "Memories: $BEFORE"

# 4. Search
echo -e "\n4. Searching for 'neural'..."
curl -s "http://localhost:8000/api/recall?q=neural&k=3" | jq -r '.[] | "\(.score | tonumber | . * 100 | round / 100) - \(.document[:50])..."'

# 5. Compact
echo -e "\n5. Running compaction..."
curl -s -X POST http://localhost:8000/api/compact | jq

# 6. Stats after
echo -e "\n6. Stats after compaction..."
AFTER=$(curl -s http://localhost:8000/api/stats | jq -r '.total_memories')
echo "Memories: $AFTER (reduced by $((BEFORE - AFTER)))"

echo -e "\n=== Test Complete ==="
```

### PowerShell Version

```powershell
Write-Host "=== TraceMind API Test ===" -ForegroundColor Cyan

# 1. Health check
Write-Host "`n1. Health check..." -ForegroundColor Yellow
curl.exe -s http://localhost:8000/health | ConvertFrom-Json

# 2. Add memories
Write-Host "`n2. Adding memories..." -ForegroundColor Yellow
1..5 | ForEach-Object {
    $body = @{
        text = "Memory $_ about neural networks"
        importance = 0.7
    } | ConvertTo-Json
    
    curl.exe -s -X POST http://localhost:8000/api/remember `
        -H "Content-Type: application/json" `
        -d $body | ConvertFrom-Json | Select-Object -ExpandProperty id
}

# 3. Stats before
Write-Host "`n3. Stats before compaction..." -ForegroundColor Yellow
$statsBefore = curl.exe -s http://localhost:8000/api/stats | ConvertFrom-Json
Write-Host "Memories: $($statsBefore.total_memories)"

# 4. Search
Write-Host "`n4. Searching for 'neural'..." -ForegroundColor Yellow
$results = curl.exe -s "http://localhost:8000/api/recall?q=neural&k=3" | ConvertFrom-Json
$results | ForEach-Object {
    Write-Host "$([math]::Round($_.score, 3)) - $($_.document.Substring(0, [Math]::Min(50, $_.document.Length)))..."
}

# 5. Compact
Write-Host "`n5. Running compaction..." -ForegroundColor Yellow
curl.exe -s -X POST http://localhost:8000/api/compact | ConvertFrom-Json

# 6. Stats after
Write-Host "`n6. Stats after compaction..." -ForegroundColor Yellow
$statsAfter = curl.exe -s http://localhost:8000/api/stats | ConvertFrom-Json
Write-Host "Memories: $($statsAfter.total_memories) (reduced by $($statsBefore.total_memories - $statsAfter.total_memories))"

Write-Host "`n=== Test Complete ===" -ForegroundColor Green
```

---

## Postman Collection

Import this JSON into Postman:

```json
{
  "info": {
    "name": "TraceMind API",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "item": [
    {
      "name": "Remember",
      "request": {
        "method": "POST",
        "header": [{"key": "Content-Type", "value": "application/json"}],
        "body": {
          "mode": "raw",
          "raw": "{\n  \"text\": \"Neural networks are ML models\",\n  \"topic\": \"ML\",\n  \"importance\": 0.9\n}"
        },
        "url": "http://localhost:8000/api/remember"
      }
    },
    {
      "name": "Recall",
      "request": {
        "method": "GET",
        "url": {
          "raw": "http://localhost:8000/api/recall?q=machine learning&k=5&decay=true",
          "query": [
            {"key": "q", "value": "machine learning"},
            {"key": "k", "value": "5"},
            {"key": "decay", "value": "true"}
          ]
        }
      }
    },
    {
      "name": "Compact",
      "request": {
        "method": "POST",
        "url": "http://localhost:8000/api/compact"
      }
    },
    {
      "name": "Stats",
      "request": {
        "method": "GET",
        "url": "http://localhost:8000/api/stats"
      }
    }
  ]
}
```

---

## Tips

- Use `jq` for JSON formatting: `curl ... | jq`
- Set `$env:PYTHONUNBUFFERED=1` for immediate output
- Check logs in backend terminal for debugging
- Use Swagger UI at http://localhost:8000/docs for interactive testing
