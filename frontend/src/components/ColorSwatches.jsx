import { swatchOf } from '../lib/colors.js'

export default function ColorSwatches({ colors = [], size = 14 }) {
  return (
    <ul className="swatches" aria-label={`Dominant colors: ${colors.join(', ')}`}>
      {colors.map((color) => (
        <li key={color} title={color} style={{ background: swatchOf(color), width: size, height: size }} />
      ))}
    </ul>
  )
}