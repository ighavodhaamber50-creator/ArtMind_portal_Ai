import { useEffect, useRef, useState } from 'react'
import { getCategories } from '../api/gallery.js'
import { addMyArtwork, deleteMyArtwork, getMyArtworks } from '../api/myArtworks.js'
import Loader from '../components/Loader.jsx'
import MyArtworkCard from '../components/MyArtworkCard.jsx'
import { MEDIUMS, STYLES, SURFACES } from '../lib/options.js'

const ACCEPTED = ['image/jpeg', 'image/png', 'image/webp']
const MAX_BYTES = 5 * 1024 * 1024
const LIMIT = 20
const EMPTY_TEXT = { title: '', artist_name: '', description: '' }

export default function MyArtworks() {
  const [list, setList] = useState({ status: 'loading', items: [], error: '' })
  const [categories, setCategories] = useState([])
  const [fields, setFields] = useState({
    ...EMPTY_TEXT, category: '', style: 'contemporary', medium: 'acrylic', surface: 'canvas',
  })
  const [file, setFile] = useState(null)
  const [preview, setPreview] = useState('')
  const [over, setOver] = useState(false)
  const [saving, setSaving] = useState(false)
  const [notice, setNotice] = useState(null) // { kind: 'success' | 'danger', text }
  const previewRef = useRef('')

  useEffect(() => {
    let cancelled = false
    getMyArtworks()
      .then((items) => {
        if (!cancelled) setList({ status: 'ready', items, error: '' })
      })
      .catch((err) => {
        if (!cancelled) setList({ status: 'error', items: [], error: err.message })
      })
    getCategories()
      .then((data) => {
        if (cancelled) return
        setCategories(data)
        setFields((current) => ({ ...current, category: current.category || String(data[0]?.id ?? '') }))
      })
      .catch(() => {})
    return () => {
      cancelled = true
    }
  }, [])

  // Free the preview picture from memory when leaving the page
  useEffect(() => () => {
    if (previewRef.current) URL.revokeObjectURL(previewRef.current)
  }, [])

  const update = (event) =>
    setFields((current) => ({ ...current, [event.target.name]: event.target.value }))

  function choose(selected) {
    if (!selected) return
    if (!ACCEPTED.includes(selected.type)) {
      setNotice({ kind: 'danger', text: 'Please choose a JPG, PNG or WEBP image.' })
      return
    }
    if (selected.size > MAX_BYTES) {
      setNotice({ kind: 'danger', text: 'That image is larger than 5 MB. Please choose a smaller one.' })
      return
    }
    if (previewRef.current) URL.revokeObjectURL(previewRef.current)
    previewRef.current = URL.createObjectURL(selected)
    setFile(selected)
    setPreview(previewRef.current)
    setNotice(null)
  }

  function clearPicture() {
    if (previewRef.current) URL.revokeObjectURL(previewRef.current)
    previewRef.current = ''
    setFile(null)
    setPreview('')
  }

  function handleDrop(event) {
    event.preventDefault()
    setOver(false)
    choose(event.dataTransfer.files?.[0])
  }

  async function handleSubmit(event) {
    event.preventDefault()
    if (!file) {
      setNotice({ kind: 'danger', text: 'Please choose a picture first.' })
      return
    }
    setSaving(true)
    setNotice(null)
    try {
      const saved = await addMyArtwork(fields, file)
      setList((current) => ({ ...current, status: 'ready', items: [saved, ...current.items] }))
      setFields((current) => ({ ...current, ...EMPTY_TEXT }))
      clearPicture()
      setNotice({ kind: 'success', text: `\u201c${saved.title}\u201d was saved. Its details are ready to download below.` })
    } catch (err) {
      setNotice({ kind: 'danger', text: err.message })
    } finally {
      setSaving(false)
    }
  }

  async function handleDelete(artwork) {
    if (!window.confirm(`Delete \u201c${artwork.title}\u201d? This cannot be undone.`)) return
    try {
      await deleteMyArtwork(artwork.id)
      setList((current) => ({ ...current, items: current.items.filter((item) => item.id !== artwork.id) }))
      setNotice({ kind: 'success', text: `\u201c${artwork.title}\u201d was deleted.` })
    } catch (err) {
      setNotice({ kind: 'danger', text: err.message })
    }
  }

  const full = list.items.length >= LIMIT

  return (
    <>
      <header className="gallery-head" data-category="nature">
        <div className="container">
          <h1>My Artworks</h1>
          <p>
            Add your own paintings and pictures, keep them in one place, and download their details
            as a PDF or a Word file. Only you can see them.
          </p>
        </div>
      </header>

      <div className="container section" style={{ paddingTop: '2.5rem' }}>
        {notice && (
          <div className={`alert alert-${notice.kind}`} role={notice.kind === 'danger' ? 'alert' : 'status'}>
            {notice.text}
          </div>
        )}

        <div className="row g-4 g-lg-5">
          <div className="col-lg-5">
            <form className="result-panel" onSubmit={handleSubmit}>
              <h2 className="h4">Add a painting</h2>

              {preview ? (
                <div className="preview-frame mb-3">
                  <img src={preview} alt="The picture you chose" />
                </div>
              ) : (
                <label
                  className={`dropzone mb-3${over ? ' is-over' : ''}`}
                  onDragOver={(event) => { event.preventDefault(); setOver(true) }}
                  onDragLeave={() => setOver(false)}
                  onDrop={handleDrop}
                >
                  <input
                    type="file"
                    accept="image/jpeg,image/png,image/webp"
                    disabled={full}
                    onChange={(event) => {
                      choose(event.target.files?.[0])
                      event.target.value = ''
                    }}
                  />
                  <i className="bi bi-cloud-arrow-up" />
                  <strong>Drop a picture here, or click to choose</strong>
                  <span className="dropzone-hint">JPG, PNG or WEBP, up to 5 MB</span>
                </label>
              )}
              {preview && (
                <button type="button" className="btn btn-outline-dark btn-sm mb-3" onClick={clearPicture}>
                  Choose another picture
                </button>
              )}

              <div className="mb-3">
                <label className="form-label" htmlFor="title">Title</label>
                <input id="title" name="title" className="form-control" value={fields.title}
                       onChange={update} maxLength={200} required />
              </div>
              <div className="mb-3">
                <label className="form-label" htmlFor="artist_name">Artist name (optional)</label>
                <input id="artist_name" name="artist_name" className="form-control" value={fields.artist_name}
                       onChange={update} maxLength={120} placeholder="Leave empty to use your username" />
              </div>

              <div className="row g-3 mb-3">
                <div className="col-sm-6">
                  <label className="form-label" htmlFor="category">Category</label>
                  <select id="category" name="category" className="form-select" value={fields.category}
                          onChange={update} required>
                    {categories.map((category) => (
                      <option key={category.id} value={category.id}>{category.name}</option>
                    ))}
                  </select>
                </div>
                <div className="col-sm-6">
                  <label className="form-label" htmlFor="style">Style</label>
                  <select id="style" name="style" className="form-select" value={fields.style} onChange={update}>
                    {STYLES.map(([value, label]) => <option key={value} value={value}>{label}</option>)}
                  </select>
                </div>
                <div className="col-sm-6">
                  <label className="form-label" htmlFor="medium">Medium</label>
                  <select id="medium" name="medium" className="form-select" value={fields.medium} onChange={update}>
                    {MEDIUMS.map(([value, label]) => <option key={value} value={value}>{label}</option>)}
                  </select>
                </div>
                <div className="col-sm-6">
                  <label className="form-label" htmlFor="surface">Surface</label>
                  <select id="surface" name="surface" className="form-select" value={fields.surface} onChange={update}>
                    {SURFACES.map(([value, label]) => <option key={value} value={value}>{label}</option>)}
                  </select>
                </div>
              </div>

              <div className="mb-3">
                <label className="form-label" htmlFor="description">Description (optional)</label>
                <textarea id="description" name="description" className="form-control" rows={3}
                          value={fields.description} onChange={update} maxLength={2000} />
              </div>

              <button className="btn btn-brand w-100" disabled={saving || full}>
                {saving ? 'Saving...' : 'Save to My Artworks'}
              </button>
              {full && (
                <p className="small text-secondary mt-2 mb-0">
                  You have reached the limit of {LIMIT} artworks. Delete one to add another.
                </p>
              )}
              <p className="small text-secondary mt-3 mb-0">
                The main colors are measured from your picture automatically.
              </p>
            </form>
          </div>

          <div className="col-lg-7">
            <div className="d-flex justify-content-between align-items-baseline mb-3">
              <h2 className="h4 mb-0">Your paintings</h2>
              <span className="text-secondary">{list.items.length} of {LIMIT} saved</span>
            </div>

            {list.status === 'loading' && <Loader label="Opening your collection..." />}
            {list.status === 'error' && <div className="alert alert-danger" role="alert">{list.error}</div>}
            {list.status === 'ready' && list.items.length === 0 && (
              <p className="text-secondary">
                Nothing here yet. Add your first painting or picture with the form, and it will appear here.
              </p>
            )}
            <div className="row g-4">
              {list.items.map((artwork) => (
                <div className="col-sm-6" key={artwork.id}>
                  <MyArtworkCard artwork={artwork} onDelete={handleDelete} />
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </>
  )
}