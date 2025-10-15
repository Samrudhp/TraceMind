import React, { useState } from 'react'
import axios from 'axios'
import { useNavigate } from 'react-router-dom'

function Remember() {
  const navigate = useNavigate()
  const [formData, setFormData] = useState({
    text: '',
    topic: '',
    importance: 0.5
  })
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError(null)
    setResult(null)

    try {
      const response = await axios.post('/api/remember', {
        text: formData.text,
        topic: formData.topic || undefined,
        importance: parseFloat(formData.importance)
      })
      
      setResult(response.data)
      
      // Reset form
      setTimeout(() => {
        setFormData({ text: '', topic: '', importance: 0.5 })
      }, 2000)
    } catch (err) {
      setError(err.response?.data?.detail || 'Error storing memory')
    } finally {
      setLoading(false)
    }
  }

  const handleChange = (e) => {
    const { name, value } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: value
    }))
  }

  return (
    <div className="max-w-3xl mx-auto">
      <div className="bg-slate-800 rounded-lg shadow-xl p-8">
        <h2 className="text-3xl font-bold mb-2 text-cyan-400">Remember</h2>
        <p className="text-slate-400 mb-6">Store a new memory in the vector database</p>

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Text Input */}
          <div>
            <label htmlFor="text" className="block text-sm font-medium text-slate-300 mb-2">
              Memory Text *
            </label>
            <textarea
              id="text"
              name="text"
              rows="6"
              required
              value={formData.text}
              onChange={handleChange}
              className="w-full px-4 py-3 bg-slate-700 border border-slate-600 rounded-lg text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-cyan-500 focus:border-transparent"
              placeholder="Enter the memory you want to store..."
            />
            <p className="mt-1 text-sm text-slate-400">
              {formData.text.length} characters
            </p>
          </div>

          {/* Topic Input */}
          <div>
            <label htmlFor="topic" className="block text-sm font-medium text-slate-300 mb-2">
              Topic (optional)
            </label>
            <input
              type="text"
              id="topic"
              name="topic"
              value={formData.topic}
              onChange={handleChange}
              className="w-full px-4 py-3 bg-slate-700 border border-slate-600 rounded-lg text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-cyan-500 focus:border-transparent"
              placeholder="e.g., ML, cooking, travel"
            />
          </div>

          {/* Importance Slider */}
          <div>
            <label htmlFor="importance" className="block text-sm font-medium text-slate-300 mb-2">
              Importance: {formData.importance}
            </label>
            <input
              type="range"
              id="importance"
              name="importance"
              min="0"
              max="1"
              step="0.1"
              value={formData.importance}
              onChange={handleChange}
              className="w-full h-2 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-cyan-500"
            />
            <div className="flex justify-between text-xs text-slate-400 mt-1">
              <span>Low (0.0)</span>
              <span>High (1.0)</span>
            </div>
          </div>

          {/* Submit Button */}
          <button
            type="submit"
            disabled={loading || !formData.text.trim()}
            className="w-full py-3 px-6 bg-cyan-600 hover:bg-cyan-700 disabled:bg-slate-600 disabled:cursor-not-allowed text-white font-semibold rounded-lg transition-colors duration-200 shadow-lg"
          >
            {loading ? 'Storing...' : 'Remember'}
          </button>
        </form>

        {/* Success Message */}
        {result && (
          <div className="mt-6 p-4 bg-green-900/50 border border-green-700 rounded-lg">
            <h3 className="font-semibold text-green-400 mb-2">✓ Memory Stored Successfully</h3>
            <p className="text-sm text-slate-300">ID: {result.id}</p>
            <p className="text-sm text-slate-400">Timestamp: {new Date(result.timestamp).toLocaleString()}</p>
            <button
              onClick={() => navigate('/dashboard')}
              className="mt-3 text-sm text-cyan-400 hover:text-cyan-300 underline"
            >
              View in Dashboard →
            </button>
          </div>
        )}

        {/* Error Message */}
        {error && (
          <div className="mt-6 p-4 bg-red-900/50 border border-red-700 rounded-lg">
            <h3 className="font-semibold text-red-400 mb-2">✗ Error</h3>
            <p className="text-sm text-slate-300">{error}</p>
          </div>
        )}
      </div>

      {/* Info Box */}
      <div className="mt-6 bg-slate-800/50 border border-slate-700 rounded-lg p-6">
        <h3 className="font-semibold text-slate-300 mb-3">💡 How it works</h3>
        <ul className="space-y-2 text-sm text-slate-400">
          <li>• Your text is converted to a 384-dimensional vector using sentence-transformers</li>
          <li>• Stored in ChromaDB with metadata (timestamp, importance, topic)</li>
          <li>• Compaction runs periodically to merge similar memories</li>
          <li>• Use Recall to retrieve memories with semantic search</li>
        </ul>
      </div>
    </div>
  )
}

export default Remember
