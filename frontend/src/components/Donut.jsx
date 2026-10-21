// A small donut: how much of `total` is `part`.
export default function Donut({ part, total, label, caption }) {
  const radius = 42
  const circumference = 2 * Math.PI * radius
  const share = total ? part / total : 0

  return (
    <figure className="donut">
      <svg viewBox="0 0 100 100" role="img" aria-label={`${label}: ${part} of ${total}`}>
        <circle className="donut-track" cx="50" cy="50" r={radius} />
        <circle
          className="donut-arc"
          cx="50"
          cy="50"
          r={radius}
          strokeDasharray={`${share * circumference} ${circumference}`}
          transform="rotate(-90 50 50)"
        />
        <text className="donut-text" x="50" y="50" textAnchor="middle" dominantBaseline="central">
          {Math.round(share * 100)}%
        </text>
      </svg>
      <figcaption>
        <strong>{label}</strong>
        <span>{caption}</span>
      </figcaption>
    </figure>
  )
}