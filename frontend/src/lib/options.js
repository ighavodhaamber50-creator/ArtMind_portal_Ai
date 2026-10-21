// Filter options. These match the choices defined in the Django Artwork model.
export const STYLES = [
  ['impressionism', 'Impressionism'], ['expressionism', 'Expressionism'], ['abstract', 'Abstract'],
  ['realism', 'Realism'], ['surrealism', 'Surrealism'], ['modern', 'Modern'],
  ['classical', 'Classical'], ['contemporary', 'Contemporary'],
]
export const MEDIUMS = [
  ['oil', 'Oil'], ['watercolor', 'Watercolor'], ['acrylic', 'Acrylic'],
  ['pastel', 'Pastel'], ['ink', 'Ink'], ['mixed', 'Mixed media'],
]
export const COLORS = [
  'blue', 'green', 'yellow', 'red', 'orange', 'purple', 'pink', 'white', 'brown', 'teal', 'gold',
]
export const SORTS = [
  ['recent', 'Newest'], ['popular', 'Most viewed'], ['trending', 'Trending'], ['alphabetical', 'A to Z'],
]

export const STYLE_LABELS = Object.fromEntries(STYLES)
export const MEDIUM_LABELS = Object.fromEntries(MEDIUMS)

export const SURFACES = [
  ['canvas', 'Canvas'], ['paper', 'Paper'], ['wood', 'Wood panel'], ['board', 'Board'],
]