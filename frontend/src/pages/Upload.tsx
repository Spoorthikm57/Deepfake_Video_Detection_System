import React, { useRef, useState } from 'react'

type AnalysisResult = {
  filename?: string
  prediction?: 'REAL' | 'FAKE'
  classification_source?: string
  confidence?: number
  error?: string
}

function isVideoFile(file: File) {
  return file.type.startsWith('video/') || /\.(mp4|mov|avi|mkv|webm|m4v)$/i.test(file.name)
}

export default function Upload() {
  const [files, setFiles] = useState<File[]>([])
  const [results, setResults] = useState<AnalysisResult[]>([])
  const [progress, setProgress] = useState(0)
  const [busy, setBusy] = useState(false)
  const videoInputRef = useRef<HTMLInputElement>(null)

  const selectVideos = (selectedFiles: FileList | null) => {
    setFiles(Array.from(selectedFiles || []).filter(isVideoFile))
  }

  const analyze = async () => {
    if (files.length === 0) return

    setBusy(true)
    setResults([])
    setProgress(0)

    try {
      const form = new FormData()
      files.forEach(file => {
        form.append('files', file)
        form.append('relative_paths', file.webkitRelativePath || '')
      })

      const response = await fetch('/predict-multi', { method: 'POST', body: form })
      const data = await response.json()
      if (!response.ok) throw new Error(data.error || 'Video analysis failed.')

      setResults(data.results || [])
      setProgress(100)
    } catch (error) {
      setResults([{ error: error instanceof Error ? error.message : 'Video analysis failed.' }])
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="container">
      <h1>Predict Videos</h1>
      <div className="card" style={{ textAlign: 'center' }}>
        <div style={{ marginBottom: 20 }}>
          <label htmlFor="videoFiles" style={{ display: 'block', marginBottom: 8, fontWeight: 600, color: '#e2e8f0' }}>
            Choose video file(s)
          </label>
          <input
            ref={videoInputRef}
            id="videoFiles"
            type="file"
            multiple
            accept="video/*"
            onChange={event => selectVideos(event.target.files)}
          />
          {files.length > 0 && <p>{files.length} video(s) selected.</p>}
        </div>

        <button className="btn" onClick={analyze} disabled={busy || files.length === 0}>
          {busy ? 'Analyzing...' : 'Analyze'}
        </button>
        <div className="progress"><div className="bar" style={{ width: progress + '%' }} /></div>
      </div>

      <div className="grid" style={{ marginTop: 16 }}>
        {results.map((result, index) => {
          const label = result.prediction || 'UNKNOWN'
          return (
            <div key={index} className="result">
              {result.error ? (
                <p role="alert">{result.error}</p>
              ) : (
                <>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
                    <strong>{result.filename || 'video'}</strong>
                    <span className={'badge ' + (label === 'REAL' ? 'real' : 'fake')}>PREDICTION: {label}</span>
                  </div>
                  <p>Classification source: {result.classification_source || 'AI Model'}</p>
                  {typeof result.confidence === 'number' && (
                    <p>Confidence: {(result.confidence * 100).toFixed(1)}%</p>
                  )}
                </>
              )}
            </div>
          )
        })}
      </div>
      <a href="/" style={{ color: '#93c5fd', textDecoration: 'none', display: 'inline-block', marginTop: 12 }}>← Back to Home</a>
    </div>
  )
}
