import { useEffect, useState } from 'react'
import { getAnalytics } from '../api/analytics.js'
import BarList from '../components/BarList.jsx'
import ColumnChart from '../components/ColumnChart.jsx'
import Donut from '../components/Donut.jsx'
import Loader from '../components/Loader.jsx'
import { swatchOf } from '../lib/colors.js'

const slug = (name) => name.toLowerCase()
const titleCase = (text) => text.charAt(0).toUpperCase() + text.slice(1)

function Metric({ value, label }) {
  return (
    <div className="metric">
      <strong>{value.toLocaleString()}</strong>
      <span>{label}</span>
    </div>
  )
}

function ChartCard({ title, hint, children }) {
  return (
    <div className="chart-card">
      <h2 className="h4">{title}</h2>
      {hint && <p className="chart-hint">{hint}</p>}
      {children}
    </div>
  )
}

export default function Analytics() {
  const [state, setState] = useState({ status: 'loading', data: null, error: '', at: null })
  const [reloadKey, setReloadKey] = useState(0)

  useEffect(() => {
    let cancelled = false
    getAnalytics()
      .then((data) => {
        if (!cancelled) setState({ status: 'ready', data, error: '', at: new Date() })
      })
      .catch((err) => {
        if (!cancelled) setState((previous) => ({ ...previous, status: 'error', error: err.message }))
      })
    return () => {
      cancelled = true
    }
  }, [reloadKey])

  function refresh() {
    setReloadKey((key) => key + 1)
  }

  const { data } = state
  if (!data) {
    if (state.status === 'error') {
      return (
        <div className="container py-5 empty-state">
          <div className="alert alert-danger" role="alert">{state.error}</div>
          <button className="btn btn-dark" onClick={() => { setState((p) => ({ ...p, status: 'loading' })); refresh() }}>
            Try again
          </button>
        </div>
      )
    }
    return <Loader label="Counting the visitors..." />
  }

  const activity = data.user_activity
  const ai = data.ai_usage

  const metrics = [
    [data.totals.artworks, 'paintings in the gallery'],
    [activity.total_users, 'registered users'],
    [activity.new_users_7d, 'new users this week'],
    [activity.active_users_7d, 'active users this week'],
    [activity.total_favorites, 'paintings saved'],
    [activity.total_artwork_views, 'painting views'],
  ]

  const mostViewed = data.most_viewed.map((artwork) => ({
    key: artwork.id, label: artwork.title, sub: artwork.artist, value: artwork.views, category: slug(artwork.category),
  }))
  const colors = data.popular_colors.map((entry) => ({
    key: entry.color, label: titleCase(entry.color), value: entry.views, color: swatchOf(entry.color),
  }))
  const trending = data.trending.map((entry) => ({ key: entry.id, label: entry.title, value: entry.views }))
  const searched = data.searched_categories.map((entry) => ({
    key: entry.category, label: entry.category, value: entry.searches, category: slug(entry.category),
  }))

  return (
    <>
      <header className="gallery-head" data-category="figurative">
        <div className="container">
          <h1>Analytics</h1>
          <p>How people are using ArtMind. Only administrators can see this page.</p>
        </div>
      </header>

      <div className="container" style={{ paddingTop: '2rem' }}>
        <div className="d-flex flex-wrap justify-content-between align-items-center gap-2 mb-3">
          <span className="text-secondary">
            Updated at {state.at.toLocaleTimeString()}
            {state.status === 'error' && ` (the last refresh failed: ${state.error})`}
          </span>
          <button className="btn btn-outline-dark btn-sm" onClick={refresh}>Refresh</button>
        </div>

        <div className="metric-grid">
          {metrics.map(([value, label]) => <Metric key={label} value={value} label={label} />)}
        </div>

        <div className="row g-4 mt-1">
          <div className="col-lg-6">
            <ChartCard title="Most viewed paintings" hint="Total views, highest first.">
              <BarList items={mostViewed} />
            </ChartCard>
          </div>
          <div className="col-lg-6">
            <ChartCard title="Popular categories" hint="Total views of the paintings in each category.">
              <ColumnChart items={data.popular_categories.map((c) => ({ label: c.name, value: c.views }))} />
            </ChartCard>
          </div>
          <div className="col-lg-6">
            <ChartCard title="Popular colors" hint="Weighted by how often each painting is viewed.">
              <BarList items={colors} />
            </ChartCard>
          </div>
          <div className="col-lg-6">
            <ChartCard title="Trending this week" hint="Paintings opened by signed-in visitors in the last 7 days.">
              <BarList items={trending} empty="No paintings have been opened in the last 7 days." />
            </ChartCard>
          </div>
          <div className="col-lg-6">
            <ChartCard title="Most searched categories" hint="From searches that named a category.">
              <BarList
                items={searched}
                empty="No category searches yet. Search from the gallery and they will show up here."
              />
            </ChartCard>
          </div>
          <div className="col-lg-6">
            <ChartCard
              title="How much real AI is used"
              hint="The rest used the built-in keyword and color methods."
            >
              <div className="donuts">
                <Donut
                  part={ai.searches_with_ai}
                  total={ai.searches_total}
                  label="Searches understood by AI"
                  caption={ai.searches_total ? `${ai.searches_with_ai} of ${ai.searches_total}` : 'No searches yet'}
                />
                <Donut
                  part={ai.analyses_real}
                  total={ai.analyses_total}
                  label="Analyses with AI category and style"
                  caption={ai.analyses_total ? `${ai.analyses_real} of ${ai.analyses_total}` : 'No analyses yet'}
                />
              </div>
            </ChartCard>
          </div>
        </div>
      </div>
    </>
  )
}