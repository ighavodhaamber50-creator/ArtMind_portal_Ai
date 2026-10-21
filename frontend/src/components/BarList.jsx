// Horizontal bar chart. Each item: { key, label, sub?, value, category?, color? }
export default function BarList({ items, empty = 'Nothing to show yet.' }) {
  if (items.length === 0) return <p className="text-secondary mb-0">{empty}</p>
  const max = Math.max(...items.map((item) => item.value), 1)

  return (
    <ul className="chart-bars">
      {items.map((item) => (
        <li key={item.key ?? item.label} data-category={item.category}>
          <span className="chart-label">
            {item.label}
            {item.sub && <small>{item.sub}</small>}
          </span>
          <span className="chart-track">
            <span
              className="chart-fill"
              style={{ width: `${(item.value / max) * 100}%`, ...(item.color ? { background: item.color } : {}) }}
            />
          </span>
          <span className="chart-value">{item.value}</span>
        </li>
      ))}
    </ul>
  )
}