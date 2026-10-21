import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { getArtworks, getCategories, searchArtworks } from '../api/gallery.js'
import ArtworkCard from '../components/ArtworkCard.jsx'
import FilterBar from '../components/FilterBar.jsx'
import Loader from '../components/Loader.jsx'
import Pager from '../components/Pager.jsx'
import { useAuth } from '../context/useAuth.js'
import { MEDIUM_LABELS, STYLE_LABELS } from '../lib/options.js'

const PAGE_SIZE = 12
const FILTER_KEYS = ['category', 'style', 'medium', 'color', 'sort']

function criteriaChips(criteria) {
  const chips = []
  if (criteria.category) chips.push(['Category', criteria.category])
  if (criteria.style) chips.push(['Style', STYLE_LABELS[criteria.style] || criteria.style])
  if (criteria.medium) chips.push(['Medium', MEDIUM_LABELS[criteria.medium] || criteria.medium])
  criteria.colors.forEach((color) => chips.push(['Color', color]))
  criteria.themes.forEach((theme) => chips.push(['Theme', theme]))
  return chips
}

export default function Gallery() {
  const { user, loading: authLoading } = useAuth()
  const userId = user?.id
  const [searchParams, setSearchParams] = useSearchParams()
  const [categories, setCategories] = useState([])
  const [result, setResult] = useState({ key: '', status: 'loading' })
  const [reloadKey, setReloadKey] = useState(0)

  // The URL is the single source of truth, so every filter combination can be shared or bookmarked
  const paramsKey = searchParams.toString()
  const requestKey = `${paramsKey}|${userId ?? 'guest'}|${reloadKey}`
  const q = searchParams.get('q') || ''
  const searching = q !== ''
  const page = Number(searchParams.get('page')) || 1
  const values = {
    category: searchParams.get('category') || '',
    style: searchParams.get('style') || '',
    medium: searchParams.get('medium') || '',
    color: searchParams.get('color') || '',
    sort: searchParams.get('sort') || 'recent',
  }
  const hasFilters = FILTER_KEYS.some((key) => searchParams.get(key))

  useEffect(() => {
    let cancelled = false
    getCategories()
      .then((data) => { if (!cancelled) setCategories(data) })
      .catch(() => {})
    return () => {
      cancelled = true
    }
  }, [])

  useEffect(() => {
    if (authLoading) return
    let cancelled = false
    const params = new URLSearchParams(paramsKey)
    const text = params.get('q') || ''

    async function load() {
      try {
        let data
        if (text) {
          data = { mode: 'search', ...(await searchArtworks(text)) }
        } else {
          const query = {}
          for (const key of [...FILTER_KEYS, 'page']) {
            if (params.get(key)) query[key] = params.get(key)
          }
          const response = await getArtworks(query)
          data = { mode: 'browse', count: response.count, results: response.results }
        }
        if (!cancelled) setResult({ key: requestKey, status: 'ready', ...data })
      } catch (err) {
        if (!cancelled) setResult({ key: requestKey, status: 'error', error: err.message })
      }
    }

    load()
    return () => {
      cancelled = true
    }
  }, [authLoading, paramsKey, requestKey])

  function setParam(key, value) {
    const next = new URLSearchParams(searchParams)
    if (value) next.set(key, value)
    else next.delete(key)
    if (key !== 'page') next.delete('page') // a new filter starts again from page 1
    setSearchParams(next)
    if (key === 'page') window.scrollTo({ top: 0 })
  }

  function submitSearch(event) {
    event.preventDefault()
    const text = String(new FormData(event.currentTarget).get('q') || '').trim()
    setSearchParams(text ? { q: text } : {})
  }

  const clearAll = () => setSearchParams({})

  const loading = authLoading || result.key !== requestKey
  const ready = !loading && result.status === 'ready'

  let subtitle = 'Loading...'
  if (ready && searching) subtitle = `Results for \u201c${q}\u201d`
  else if (ready) subtitle = `${result.count} ${result.count === 1 ? 'painting' : 'paintings'}`

  let content
  if (loading) {
    content = <Loader label="Hanging paintings..." />
  } else if (result.status === 'error') {
    content = (
      <div className="empty-state">
        <div className="alert alert-danger" role="alert">{result.error}</div>
        <button className="btn btn-dark" onClick={() => setReloadKey((key) => key + 1)}>Try again</button>
      </div>
    )
  } else if (result.results.length === 0) {
    content = (
      <div className="empty-state">
        <h2 className="h3">Nothing here yet</h2>
        <p>
          {searching
            ? result.message
            : 'No paintings match these filters. Remove a filter to see more.'}
        </p>
        <button className="btn btn-dark" onClick={clearAll}>
          {searching ? 'Browse all paintings' : 'Clear filters'}
        </button>
      </div>
    )
  } else {
    content = (
      <>
        {result.relaxed && result.message && (
          <div className="alert alert-info" role="status">{result.message}</div>
        )}
        <div className="row g-4">
          {result.results.map((artwork) => (
            <div className="col-sm-6 col-lg-4 col-xl-3" key={artwork.id}>
              <ArtworkCard artwork={artwork} />
            </div>
          ))}
        </div>
        {result.mode === 'browse' && (
          <Pager page={page} pages={Math.ceil(result.count / PAGE_SIZE)} onPage={(next) => setParam('page', String(next))} />
        )}
      </>
    )
  }

  return (
    <>
      <header
        className="gallery-head"
        data-category={!searching && values.category ? values.category : undefined}
      >
        <div className="container">
          <h1>Gallery</h1>
          <p>{subtitle}</p>
          <form className="hero-search" key={q} onSubmit={submitSearch} role="search">
            <input
              name="q"
              type="search"
              defaultValue={q}
              aria-label="Search paintings"
              placeholder="Try: modern abstract paintings with blue colors"
              maxLength={300}
            />
            <button className="btn btn-dark" type="submit">Search</button>
          </form>
        </div>
      </header>

      <div className="container pb-4">
        {searching ? (
          ready && result.criteria && (
            <div className="criteria-row">
              <span>Understood as</span>
              {criteriaChips(result.criteria).map(([label, value]) => (
                <span className="criteria-chip" key={`${label}-${value}`}><small>{label}</small>{value}</span>
              ))}
              <span
                className={`engine-badge${result.used_ai ? '' : ' is-fallback'}`}
                title={result.note || 'Interpreted by an AI model'}
              >
                {result.used_ai ? 'Understood by AI' : 'Understood by keyword matching'}
              </span>
              <button className="btn btn-outline-dark btn-sm" onClick={clearAll}>Clear search</button>
            </div>
          )
        ) : (
          <FilterBar
            categories={categories}
            values={values}
            onChange={setParam}
            onClear={clearAll}
            hasFilters={hasFilters}
          />
        )}
        {content}
      </div>
    </>
  )
}