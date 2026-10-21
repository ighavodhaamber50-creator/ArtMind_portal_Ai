import { swatchOf } from '../lib/colors.js'
import { COLORS, MEDIUMS, SORTS, STYLES } from '../lib/options.js'

export default function FilterBar({ categories, values, onChange, onClear, hasFilters }) {
  return (
    <div className="filter-bar">
      <div className="cat-chips" role="group" aria-label="Category">
        <button
          type="button"
          className="cat-chip"
          aria-pressed={!values.category}
          onClick={() => onChange('category', '')}
        >
          All
        </button>
        {categories.map((category) => (
          <button
            key={category.id}
            type="button"
            className="cat-chip"
            data-category={category.slug}
            aria-pressed={values.category === category.slug}
            onClick={() => onChange('category', values.category === category.slug ? '' : category.slug)}
          >
            {category.name}
          </button>
        ))}
      </div>

      <div className="filter-row">
        <label className="filter-field">
          Style
          <select className="form-select form-select-sm" value={values.style}
                  onChange={(event) => onChange('style', event.target.value)}>
            <option value="">Any style</option>
            {STYLES.map(([value, label]) => <option key={value} value={value}>{label}</option>)}
          </select>
        </label>

        <label className="filter-field">
          Medium
          <select className="form-select form-select-sm" value={values.medium}
                  onChange={(event) => onChange('medium', event.target.value)}>
            <option value="">Any medium</option>
            {MEDIUMS.map(([value, label]) => <option key={value} value={value}>{label}</option>)}
          </select>
        </label>

        <div className="filter-field">
          Color
          <div className="color-dots" role="group" aria-label="Color">
            {COLORS.map((color) => (
              <button
                key={color}
                type="button"
                className="color-dot"
                title={color}
                aria-label={`Color ${color}`}
                aria-pressed={values.color === color}
                style={{ background: swatchOf(color) }}
                onClick={() => onChange('color', values.color === color ? '' : color)}
              />
            ))}
          </div>
        </div>

        <label className="filter-field">
          Sort by
          <select className="form-select form-select-sm" value={values.sort}
                  onChange={(event) => onChange('sort', event.target.value)}>
            {SORTS.map(([value, label]) => <option key={value} value={value}>{label}</option>)}
          </select>
        </label>

        {hasFilters && (
          <button type="button" className="btn btn-outline-dark btn-sm" onClick={onClear}>
            Clear filters
          </button>
        )}
      </div>
    </div>
  )
}