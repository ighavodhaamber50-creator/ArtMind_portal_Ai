// Vertical column chart. Each item: { label, value }. Colors come from the category name.
export default function ColumnChart({ items, empty = 'Nothing to show yet.' }) {
  if (items.length === 0) return <p className="text-secondary mb-0">{empty}</p>
  const max = Math.max(...items.map((item) => item.value), 1)

  return (
    <div className="columns">
      {items.map((item) => (
        <div className="column" key={item.label} data-category={item.label.toLowerCase()}>
          <span className="column-value">{item.value}</span>
          <div className="column-track">
            <div className="column-bar" style={{ height: `${Math.max((item.value / max) * 100, 2)}%` }} />
          </div>
          <span className="column-label">{item.label}</span>
        </div>
      ))}
    </div>
  )
}