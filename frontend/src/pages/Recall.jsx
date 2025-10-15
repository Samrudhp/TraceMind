import React, { useState } from 'react'
import axios from 'axios'

function Recall() {
  const [query, setQuery] = useState('')
  const [k, setK] = useState(5)
  const [decay, setDecay] = useState(true)
  const [topic, setTopic] = useState('')
  const [loading, setLoading] = useState(false)
  const [results, setResults] = useState([])
  const [error, setError] = useState(null)

  const handleSearch = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError(null)
    setResults([])

    try {
      const params = {
        q: query,
        k: k,
        decay: decay
      }
      if (topic.trim()) {
        params.topic = topic.trim()
      }

      const response = await axios.get('/api/recall', { params })
      setResults(response.data)
    } catch (err) {
      setError(err.response?.data?.detail || 'Error recalling memories')
    } finally {
      setLoading(false)
    }
  }

  const handleReRemember = async (memory) => {
    try {
      await axios.post('/api/remember', {
        text: memory.document,
        topic: memory.metadata.topic,
        importance: memory.metadata.importance
      })
      alert('Memory rehearsed successfully!')
    } catch (err) {
      alert('Error rehearsing memory: ' + (err.response?.data?.detail || err.message))
    }
  }

  const getScoreColor = (score) => {
    if (score >= 0.8) return 'text-green-400'
    if (score >= 0.6) return 'text-yellow-400'
    return 'text-orange-400'
  }

  const getAgeLabel = (days) => {
    if (days < 1) return 'Today'
    if (days < 7) return `${Math.floor(days)}d ago`
    if (days < 30) return `${Math.floor(days / 7)}w ago`
    return `${Math.floor(days / 30)}mo ago`
  }

  return (
    <div className="max-w-5xl mx-auto">
      {/* Search Form */}
      <div className="bg-slate-800 rounded-lg shadow-xl p-8 mb-6">
        <h2 className="text-3xl font-bold mb-2 text-cyan-400">Recall</h2>
        <p className="text-slate-400 mb-6">Query your memories with semantic search</p>

        <form onSubmit={handleSearch} className="space-y-4">
          {/* Query Input */}
          <div>
            <label htmlFor="query" className="block text-sm font-medium text-slate-300 mb-2">
              Query *
            </label>
            <input
              type="text"
              id="query"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              required
              className="w-full px-4 py-3 bg-slate-700 border border-slate-600 rounded-lg text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-cyan-500 focus:border-transparent"
              placeholder="What would you like to recall?"
            />
          </div>

          {/* Options Row */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* K Selector */}
            <div>
              <label htmlFor="k" className="block text-sm font-medium text-slate-300 mb-2">
                Results (k)
              </label>
              <input
                type="number"
                id="k"
                value={k}
                onChange={(e) => setK(parseInt(e.target.value))}
                min="1"
                max="50"
                className="w-full px-4 py-3 bg-slate-700 border border-slate-600 rounded-lg text-slate-100 focus:outline-none focus:ring-2 focus:ring-cyan-500 focus:border-transparent"
              />
            </div>

            {/* Topic Filter */}
            <div>
              <label htmlFor="topic" className="block text-sm font-medium text-slate-300 mb-2">
                Topic Filter
              </label>
              <input
                type="text"
                id="topic"
                value={topic}
                onChange={(e) => setTopic(e.target.value)}
                className="w-full px-4 py-3 bg-slate-700 border border-slate-600 rounded-lg text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-cyan-500 focus:border-transparent"
                placeholder="Optional"
              />
            </div>

            {/* Decay Toggle */}
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Temporal Decay
              </label>
              <label className="flex items-center cursor-pointer">
                <div className="relative">
                  <input
                    type="checkbox"
                    checked={decay}
                    onChange={(e) => setDecay(e.target.checked)}
                    className="sr-only"
                  />
                  <div className={`block w-14 h-8 rounded-full ${decay ? 'bg-cyan-600' : 'bg-slate-600'}`}></div>
                  <div className={`dot absolute left-1 top-1 bg-white w-6 h-6 rounded-full transition ${decay ? 'transform translate-x-6' : ''}`}></div>
                </div>
                <span className="ml-3 text-slate-300">{decay ? 'ON' : 'OFF'}</span>
              </label>
            </div>
          </div>

          {/* Submit Button */}
          <button
            type="submit"
            disabled={loading || !query.trim()}
            className="w-full py-3 px-6 bg-cyan-600 hover:bg-cyan-700 disabled:bg-slate-600 disabled:cursor-not-allowed text-white font-semibold rounded-lg transition-colors duration-200 shadow-lg"
          >
            {loading ? 'Searching...' : 'Recall Memories'}
          </button>
        </form>

        {/* Error Message */}
        {error && (
          <div className="mt-4 p-4 bg-red-900/50 border border-red-700 rounded-lg">
            <p className="text-sm text-slate-300">{error}</p>
          </div>
        )}
      </div>

      {/* Results */}
      {results.length > 0 && (
        <div className="space-y-4">
          <h3 className="text-xl font-semibold text-slate-300">
            Found {results.length} {results.length === 1 ? 'memory' : 'memories'}
          </h3>
          
          {results.map((result, index) => (
            <div
              key={result.id}
              className="bg-slate-800 rounded-lg shadow-lg p-6 border border-slate-700 hover:border-cyan-600 transition"
            >
              {/* Header */}
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center space-x-3">
                  <span className="text-2xl font-bold text-slate-600">#{index + 1}</span>
                  <div>
                    <span className={`text-2xl font-bold ${getScoreColor(result.score)}`}>
                      {result.score.toFixed(3)}
                    </span>
                    <span className="text-sm text-slate-400 ml-2">
                      (raw: {result.raw_similarity.toFixed(3)})
                    </span>
                  </div>
                </div>
                <button
                  onClick={() => handleReRemember(result)}
                  className="px-3 py-1 text-xs bg-slate-700 hover:bg-slate-600 text-slate-300 rounded transition"
                  title="Re-remember (rehearsal)"
                >
                  🔄 Rehearse
                </button>
              </div>

              {/* Document Text */}
              <p className="text-slate-200 mb-4 leading-relaxed">{result.document}</p>

              {/* Metadata */}
              <div className="flex flex-wrap gap-3 text-sm">
                <span className="px-2 py-1 bg-slate-700 rounded text-slate-300">
                  📅 {getAgeLabel(result.age_days)}
                </span>
                <span className="px-2 py-1 bg-slate-700 rounded text-slate-300">
                  ⚡ Importance: {result.metadata.importance.toFixed(2)}
                </span>
                {result.metadata.topic && (
                  <span className="px-2 py-1 bg-cyan-900/50 rounded text-cyan-300">
                    🏷️ {result.metadata.topic}
                  </span>
                )}
                {result.metadata.merge_count > 0 && (
                  <span className="px-2 py-1 bg-purple-900/50 rounded text-purple-300">
                    🔗 Merged: {result.metadata.merge_count}x
                  </span>
                )}
                <span className="px-2 py-1 bg-slate-700 rounded text-slate-400 text-xs">
                  ID: {result.id.slice(0, 8)}...
                </span>
              </div>
            </div>
          ))}
        </div>
      )}

      {results.length === 0 && !loading && !error && query && (
        <div className="text-center py-12 bg-slate-800 rounded-lg">
          <p className="text-slate-400">No memories found matching your query.</p>
        </div>
      )}
    </div>
  )
}

export default Recall
