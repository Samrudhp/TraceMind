import React, { useState, useEffect } from 'react'
import axios from 'axios'
import Plot from 'react-plotly.js'

function Dashboard() {
  const [stats, setStats] = useState(null)
  const [collections, setCollections] = useState([])
  const [umapData, setUmapData] = useState(null)
  const [compactionLog, setCompactionLog] = useState([])
  const [selectedPoint, setSelectedPoint] = useState(null)
  const [loading, setLoading] = useState(false)
  const [compacting, setCompacting] = useState(false)

  useEffect(() => {
    loadDashboardData()
  }, [])

  const loadDashboardData = async () => {
    setLoading(true)
    try {
      // Load stats
      const statsRes = await axios.get('/api/stats')
      setStats(statsRes.data)

      // Load collections
      const collectionsRes = await axios.get('/api/collections')
      setCollections(collectionsRes.data)

      // Load UMAP projection
      const umapRes = await axios.get('/api/dashboard/umap?n=500')
      setUmapData(umapRes.data)

      // Load compaction log
      const logRes = await axios.get('/api/dashboard/compaction-log?limit=50')
      setCompactionLog(logRes.data.events || [])
    } catch (err) {
      console.error('Error loading dashboard data:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleCompact = async () => {
    if (!confirm('Run compaction now? This will merge similar memories.')) return

    setCompacting(true)
    try {
      const response = await axios.post('/api/compact')
      alert(`Compaction complete!\nBefore: ${response.data.before_count}\nAfter: ${response.data.after_count}\nClusters merged: ${response.data.clusters_merged}`)
      
      // Reload data
      await loadDashboardData()
    } catch (err) {
      alert('Error during compaction: ' + (err.response?.data?.detail || err.message))
    } finally {
      setCompacting(false)
    }
  }

  const getTopicColor = (topic) => {
    const colors = {
      'ML': '#3b82f6',
      'cooking': '#f59e0b',
      'travel': '#10b981',
      'work': '#8b5cf6',
      'personal': '#ec4899'
    }
    return colors[topic] || '#6b7280'
  }

  const renderUmapPlot = () => {
    if (!umapData || !umapData.points || umapData.points.length === 0) {
      return (
        <div className="bg-slate-700 rounded-lg p-8 text-center">
          <p className="text-slate-400">Not enough data for visualization (need at least 2 memories)</p>
        </div>
      )
    }

    const points = umapData.points

    // Group by topic for coloring
    const topics = [...new Set(points.map(p => p.metadata.topic || 'untagged'))]
    
    const traces = topics.map(topic => {
      const topicPoints = points.filter(p => (p.metadata.topic || 'untagged') === topic)
      
      return {
        x: topicPoints.map(p => p.x),
        y: topicPoints.map(p => p.y),
        mode: 'markers',
        type: 'scatter',
        name: topic,
        marker: {
          size: topicPoints.map(p => 8 + p.metadata.importance * 8),
          color: getTopicColor(topic),
          opacity: 0.7,
          line: {
            color: 'white',
            width: 1
          }
        },
        text: topicPoints.map(p => 
          `${p.document.slice(0, 100)}...\n` +
          `Topic: ${p.metadata.topic || 'none'}\n` +
          `Age: ${Math.floor(p.age_days)}d\n` +
          `Importance: ${p.metadata.importance.toFixed(2)}\n` +
          `Merges: ${p.metadata.merge_count || 0}`
        ),
        hoverinfo: 'text',
        customdata: topicPoints.map((p, i) => i)
      }
    })

    return (
      <Plot
        data={traces}
        layout={{
          title: {
            text: `Memory Embedding Space (${umapData.projection_method})`,
            font: { color: '#e2e8f0' }
          },
          paper_bgcolor: '#1e293b',
          plot_bgcolor: '#334155',
          xaxis: {
            title: 'Dimension 1',
            gridcolor: '#475569',
            color: '#94a3b8'
          },
          yaxis: {
            title: 'Dimension 2',
            gridcolor: '#475569',
            color: '#94a3b8'
          },
          hovermode: 'closest',
          legend: {
            font: { color: '#e2e8f0' },
            bgcolor: '#1e293b'
          },
          height: 600
        }}
        config={{
          displayModeBar: true,
          displaylogo: false
        }}
        style={{ width: '100%' }}
        onClick={(data) => {
          if (data.points && data.points.length > 0) {
            const pointIndex = data.points[0].pointIndex
            const topic = data.points[0].data.name
            const topicPoints = points.filter(p => (p.metadata.topic || 'untagged') === topic)
            setSelectedPoint(topicPoints[pointIndex])
          }
        }}
      />
    )
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-slate-400">Loading dashboard...</div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-3xl font-bold text-cyan-400">Dashboard</h2>
        <button
          onClick={handleCompact}
          disabled={compacting}
          className="px-4 py-2 bg-purple-600 hover:bg-purple-700 disabled:bg-slate-600 text-white font-semibold rounded-lg transition shadow-lg"
        >
          {compacting ? 'Compacting...' : '🗜️ Run Compaction'}
        </button>
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
            <div className="text-3xl font-bold text-cyan-400">{stats.total_memories}</div>
            <div className="text-sm text-slate-400 mt-1">Total Memories</div>
          </div>
          <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
            <div className="text-3xl font-bold text-purple-400">{stats.total_merges}</div>
            <div className="text-sm text-slate-400 mt-1">Total Merges</div>
          </div>
          <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
            <div className="text-3xl font-bold text-green-400">{stats.average_age_days.toFixed(1)}d</div>
            <div className="text-sm text-slate-400 mt-1">Average Age</div>
          </div>
          <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
            <div className="text-3xl font-bold text-yellow-400">{Object.keys(stats.topics).length}</div>
            <div className="text-sm text-slate-400 mt-1">Topics</div>
          </div>
        </div>
      )}

      {/* Collections */}
      <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
        <h3 className="text-xl font-semibold text-slate-300 mb-4">ChromaDB Collections</h3>
        <div className="space-y-2">
          {collections.map(col => (
            <div key={col.name} className="flex items-center justify-between p-3 bg-slate-700 rounded">
              <div>
                <span className="font-medium text-slate-200">{col.name}</span>
                {col.metadata?.description && (
                  <span className="text-sm text-slate-400 ml-2">— {col.metadata.description}</span>
                )}
              </div>
              <span className="text-cyan-400 font-semibold">{col.count} items</span>
            </div>
          ))}
        </div>
      </div>

      {/* Topics Distribution */}
      {stats && Object.keys(stats.topics).length > 0 && (
        <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
          <h3 className="text-xl font-semibold text-slate-300 mb-4">Topics Distribution</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {Object.entries(stats.topics).map(([topic, count]) => (
              <div key={topic} className="bg-slate-700 rounded p-3">
                <div className="text-lg font-bold text-slate-200">{count}</div>
                <div className="text-sm text-slate-400">{topic}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* UMAP Visualization */}
      <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
        <h3 className="text-xl font-semibold text-slate-300 mb-4">Memory Embedding Space</h3>
        {renderUmapPlot()}
      </div>

      {/* Selected Point Details */}
      {selectedPoint && (
        <div className="bg-slate-800 rounded-lg p-6 border border-cyan-600">
          <h3 className="text-xl font-semibold text-cyan-400 mb-4">Selected Memory</h3>
          <div className="space-y-3">
            <p className="text-slate-200">{selectedPoint.document}</p>
            <div className="flex flex-wrap gap-2">
              <span className="px-2 py-1 bg-slate-700 rounded text-sm text-slate-300">
                ID: {selectedPoint.id.slice(0, 8)}
              </span>
              <span className="px-2 py-1 bg-slate-700 rounded text-sm text-slate-300">
                Age: {Math.floor(selectedPoint.age_days)}d
              </span>
              <span className="px-2 py-1 bg-slate-700 rounded text-sm text-slate-300">
                Importance: {selectedPoint.metadata.importance.toFixed(2)}
              </span>
              {selectedPoint.metadata.topic && (
                <span className="px-2 py-1 bg-cyan-900/50 rounded text-sm text-cyan-300">
                  Topic: {selectedPoint.metadata.topic}
                </span>
              )}
              {selectedPoint.metadata.merge_count > 0 && (
                <span className="px-2 py-1 bg-purple-900/50 rounded text-sm text-purple-300">
                  Merges: {selectedPoint.metadata.merge_count}
                </span>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Compaction Log */}
      <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
        <h3 className="text-xl font-semibold text-slate-300 mb-4">Compaction History</h3>
        {compactionLog.length === 0 ? (
          <p className="text-slate-400">No compaction events yet</p>
        ) : (
          <div className="space-y-2 max-h-96 overflow-y-auto">
            {compactionLog.slice().reverse().map((event, idx) => (
              <div key={idx} className="p-3 bg-slate-700 rounded text-sm">
                <div className="flex items-start justify-between">
                  <div>
                    <span className="font-semibold text-purple-400">
                      Merged {event.cluster_size} memories
                    </span>
                    <p className="text-slate-400 text-xs mt-1">
                      {new Date(event.timestamp).toLocaleString()}
                    </p>
                    <p className="text-slate-300 text-xs mt-2 line-clamp-2">
                      "{event.representative_text}"
                    </p>
                  </div>
                  <span className="text-xs text-slate-400">
                    → {event.new_id.slice(0, 8)}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

export default Dashboard
