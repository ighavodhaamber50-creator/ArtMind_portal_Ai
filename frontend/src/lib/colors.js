// Display colours for the colour names stored on each painting.
export const SWATCH = {
  blue: '#3342e8', green: '#1f9d6b', yellow: '#f5c518', red: '#d9362b', orange: '#f28a1d',
  purple: '#7a4dd8', pink: '#f07ba6', white: '#f4f4f2', brown: '#7a4e2d', teal: '#14a3a3',
  gold: '#d4af37', black: '#1b1740', gray: '#8a8fa3',
}

// Deep "painted wall" tones. White text stays readable on every one of them.
export const WALL = {
  blue: '#2a34c4', green: '#0a6f58', yellow: '#9a6200', red: '#b3261e', orange: '#b8480f',
  purple: '#5b33b5', pink: '#b02a63', white: '#343a66', brown: '#6b4226', teal: '#0b6e73',
  gold: '#8f6a0a', black: '#1b1740', gray: '#4b5068',
}

export const swatchOf = (name) => SWATCH[name] || '#8a8fa3'
export const wallOf = (name) => WALL[name] || WALL.blue