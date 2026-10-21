import { useEffect, useRef, useState } from 'react'
import { analyzeImage } from '../api/analyze.js'
import ArtworkCard from '../components/ArtworkCard.jsx'
import { swatchOf } from '../lib/colors.js'

const ACCEPTED = ['image/jpeg', 'image/png', 'image/webp']
const MAX_BYTES = 5 * 1024 * 1024

const METHOD_LABELS = {
  'opencv-kmeans': 'Measured with OpenCV',
  'openai-vision': 'Identified by an AI vision model',
  'color-matching-estimate': 'Demo estimate from color similarity, not AI',
}

function Results({ result }) {
  const isDemo = result.is_demo_result

  return (
    <div className="result-panel" aria-live="polite">
      <div className="result-row">
        <h2 className="h4 mb-0">Palette</h2>
        <span className="method">{METHOD_LABELS[result.methods.colors]}</span>
      </div>
      <div
        className="palette-big"
        role="img"
        aria-label={`Palette: ${result.palette.map((c) => `${c.name} ${c.percent}%`).join(', ')}`}
      >
        {result.palette.map((color, index) => (
          <span key={index} style={{ flexGrow: Math.max(color.percent, 1), background: color.hex }} />
        ))}
      </div>
      <ul className="palette-list">
        {result.palette.map((color, index) => (
          <li key={index}>
            <i style={{ background: color.hex }} />
            <span>{color.name} <small>{color.percent}% {color.hex}</small></span>
          </li>
        ))}
      </ul>

      <dl className="facts mt-4">
        <dt>Category</dt>
        <dd>
          {result.category || 'Not determined'}
          <div className="method">{METHOD_LABELS[result.methods.category]}</div>
        </dd>
        <dt>Style</dt>
        <dd>
          {result.style_label || 'Not determined'}
          <div className="method">{METHOD_LABELS[result.methods.style]}</div>
        </dd>
        <dt>Main colors</dt>
        <dd>
          <ul className="named-swatches">
            {result.dominant_colors.map((name) => (
              <li key={name}><i style={{ background: swatchOf(name) }} />{name}</li>
            ))}
          </ul>
        </dd>
      </dl>

      <div className="d-flex flex-wrap align-items-center gap-2">
        <span className={`engine-badge${isDemo ? ' is-fallback' : ''}`}>
          {isDemo ? 'Demo result' : 'AI result'}
        </span>
        <span className="text-secondary">{result.notice}</span>
      </div>
    </div>
  )
}

export default function Analyze() {
  const [file, setFile] = useState(null)
  const [preview, setPreview] = useState('')
  const [over, setOver] = useState(false)
  const [state, setState] = useState({ status: 'idle' })
  const previewRef = useRef('')

  // Free the preview image from memory when leaving the page
  useEffect(() => () => {
    if (previewRef.current) URL.revokeObjectURL(previewRef.current)
  }, [])

  function choose(selected) {
    if (!selected) return
    if (!ACCEPTED.includes(selected.type)) {
      setState({ status: 'error', error: 'Please choose a JPG, PNG or WEBP image.' })
      return
    }
    if (selected.size > MAX_BYTES) {
      setState({ status: 'error', error: 'That image is larger than 5 MB. Please choose a smaller one.' })
      return
    }
    if (previewRef.current) URL.revokeObjectURL(previewRef.current)
    previewRef.current = URL.createObjectURL(selected)
    setFile(selected)
    setPreview(previewRef.current)
    setState({ status: 'idle' })
  }

  function clear() {
    if (previewRef.current) URL.revokeObjectURL(previewRef.current)
    previewRef.current = ''
    setFile(null)
    setPreview('')
    setState({ status: 'idle' })
  }

  function handleDrop(event) {
    event.preventDefault()
    setOver(false)
    choose(event.dataTransfer.files?.[0])
  }

  async function handleSubmit(event) {
    event.preventDefault()
    if (!file) return
    setState({ status: 'analyzing' })
    try {
      setState({ status: 'done', result: await analyzeImage(file) })
    } catch (err) {
      setState({ status: 'error', error: err.message })
    }
  }

  const busy = state.status === 'analyzing'

  return (
    <>
      <header className="gallery-head" data-category="landscape">
        <div className="container">
          <h1>Analyze Artwork</h1>
          <p>Upload a photo of a painting to read its palette and find its closest matches in the gallery.</p>
        </div>
      </header>

      <div className="container section" style={{ paddingTop: '2.5rem' }}>
        <div className="row g-4 g-lg-5">
          <div className="col-lg-5">
            <form onSubmit={handleSubmit}>
              {preview ? (
                <div className="preview-frame">
                  <img src={preview} alt="The painting you chose" />
                </div>
              ) : (
                <label
                  className={`dropzone${over ? ' is-over' : ''}`}
                  onDragOver={(event) => { event.preventDefault(); setOver(true) }}
                  onDragLeave={() => setOver(false)}
                  onDrop={handleDrop}
                >
                  <input
                    type="file"
                    accept="image/jpeg,image/png,image/webp"
                    onChange={(event) => {
                      choose(event.target.files?.[0])
                      event.target.value = '' // lets the same file be chosen again
                    }}
                  />
                  <i className="bi bi-cloud-arrow-up" />
                  <strong>Drop a painting here, or click to choose</strong>
                  <span className="dropzone-hint">JPG, PNG or WEBP, up to 5 MB</span>
                </label>
              )}

              {state.status === 'error' && (
                <div className="alert alert-danger mt-3" role="alert">{state.error}</div>
              )}

              <div className="d-flex flex-wrap gap-2 mt-3">
                <button className="btn btn-brand" type="submit" disabled={!file || busy}>
                  {busy ? 'Mixing the palette...' : 'Analyze painting'}
                </button>
                {file && (
                  <button className="btn btn-outline-dark" type="button" onClick={clear} disabled={busy}>
                    Choose another
                  </button>
                )}
              </div>

              <p className="small text-secondary mt-3">
                Uploaded images are saved on the server with their analysis. If an AI service is
                configured, the image is also sent to it.
              </p>
            </form>
          </div>

          <div className="col-lg-7">
            {state.status === 'done' ? (
              <Results result={state.result} />
            ) : (
              <div className="result-panel">
                <h2 className="h4">How it works</h2>
                <ol className="how-list">
                  <li>Your image is shrunk and its pixels are grouped into a handful of color families.</li>
                  <li>Each color family is named, with the share of the picture it covers.</li>
                  <li>The gallery is searched for paintings with a similar palette.</li>
                  <li>Category and style come from an AI vision model when one is set up. Otherwise they
                      are a rough estimate, and the result says so.</li>
                </ol>
              </div>
            )}
          </div>
        </div>

        {state.status === 'done' && state.result.similar_artworks.length > 0 && (
          <section className="section">
            <div className="section-head">
              <h2>Closest paintings in the gallery</h2>
              <p>Ranked by how much of your image&rsquo;s color appears in each painting.</p>
            </div>
            <div className="row g-4">
              {state.result.similar_artworks.map((artwork) => (
                <div className="col-sm-6 col-lg-4" key={artwork.id}>
                  <ArtworkCard
                    artwork={artwork}
                    note={`${artwork.match_percent}% of your image's colors appear in this painting`}
                  />
                </div>
              ))}
            </div>
          </section>
        )}
      </div>
    </>
  )
}