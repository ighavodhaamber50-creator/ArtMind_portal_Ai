"""Built-in art knowledge, used by the assistant when no AI service is available."""

STYLE_FACTS = {
    'impressionism': (
        'Impressionism began in 19th-century France. Painters such as Claude Monet and '
        'Pierre-Auguste Renoir used quick, visible brushstrokes to capture the changing effects '
        'of light and color, often painting outdoors. Everyday scenes and landscapes were '
        'popular subjects.'),
    'expressionism': (
        'Expressionism emerged in early 20th-century Europe. Artists such as Edvard Munch and '
        'Ernst Ludwig Kirchner distorted shapes and used intense, non-realistic color to '
        'express emotion rather than show things exactly as they look.'),
    'realism': (
        'Realism rose in mid-19th-century France and shows ordinary subjects as they really '
        'appear, without idealizing them. Gustave Courbet is a leading example. Today the word '
        '"realistic" also describes highly accurate, lifelike painting.'),
    'surrealism': (
        'Surrealism began in the 1920s and explores dreams and the unconscious by combining '
        'ordinary things in unexpected ways. Salvador Dali and Rene Magritte are two of its '
        'best-known painters.'),
    'abstract': (
        'Abstract art does not try to show a recognizable scene. It uses shape, color, line and '
        'texture on their own. Wassily Kandinsky and Piet Mondrian were early pioneers.'),
    'modern': (
        'Modern art broadly means art from the late 19th to the mid-20th century that broke '
        'away from traditional realism, including movements like Impressionism, Cubism and '
        'Expressionism. In this gallery, "Modern" is a general label for fresh, non-traditional '
        'work.'),
    'classical': (
        'Classical painting follows traditions from ancient Greece and Rome and the '
        'Renaissance: balanced composition, careful drawing and idealized forms. Religious and '
        'historical subjects were very common.'),
    'contemporary': (
        'Contemporary art is made by living artists today, roughly since the late 20th century. '
        'It mixes styles and materials freely and often reflects current ideas.'),
}

MEDIUM_FACTS = {
    'oil': (
        'Oil paint mixes pigment with oil, often linseed. It dries slowly, so you can blend and '
        'rework it for days, and it gives rich, deep color and visible texture. It is usually '
        'used on canvas or wood panels.'),
    'watercolor': (
        'Watercolor uses pigment with a water-soluble binder, applied in thin, transparent '
        'washes, usually on paper. The white of the paper provides the lights, and it dries '
        'fast, so mistakes are hard to correct.'),
    'acrylic': (
        'Acrylic paint is water-based but dries into a flexible, water-resistant film. It dries '
        'quickly, can be thinned like watercolor or used thickly like oil, and works on canvas, '
        'paper or wood.'),
    'pastel': (
        'Pastels are sticks of pigment with very little binder. They give vivid, velvety color '
        'and are blended with fingers or tools, usually on textured paper.'),
    'ink': (
        'Ink painting uses liquid ink applied with a brush or pen. It gives strong lines and '
        'tonal washes, usually on paper.'),
    'mixed': (
        'Mixed media combines more than one material, such as paint with ink or collage, in the '
        'same artwork.'),
}

TECHNIQUE_FACTS = {
    'impasto': (
        'Impasto means applying paint so thickly that brushstrokes or palette-knife marks stay '
        'visible, giving the surface real texture.'),
    'glazing': (
        'Glazing means painting thin, transparent layers of color over a dry layer, which '
        'creates depth and a glowing effect. It is common in oil painting.'),
    'wash': (
        'A wash is a thin, diluted layer of paint, usually watercolor or ink, spread '
        'evenly to cover an area with soft, transparent color.'),
}

# (words that trigger it, answer). Used for "how do I ..." questions about the website.
NAVIGATION = [
    ({'favorite', 'favorites', 'favourite', 'favourites', 'save', 'saved'},
     'Log in, then press the heart on any painting card, or use Add to Favorites on its '
     'details page. Your saved paintings appear in My Collection.'),
    ({'upload', 'analyze', 'analyse', 'recognition', 'recognize', 'identify', 'scan'},
     'Open the Analyze Artwork page and upload a photo of a painting (JPG or PNG). The app '
     'reports its likely category, style and dominant colors, and suggests similar paintings '
     'from the gallery.'),
    ({'search', 'filter', 'sort', 'find'},
     'Use the search bar on Home or Gallery and type naturally, for example "watercolor '
     'landscape paintings". The Gallery page also has filters for category, style, medium and '
     'color, and sorting by popular, recent, alphabetical or trending.'),
        ({'dashboard', 'collection', 'collections', 'library', 'recommended', 'recommendations',
      'history', 'viewed'},
     'After you log in, open My Collection to see recently viewed paintings, favorites, your '
     'favorite categories, recommendations and curated picks.'),
    ({'login', 'log', 'register', 'signup', 'sign', 'account', 'logout'},
     'Use Register to create an account, then Log in. You need an account to save favorites '
     'and get personalized recommendations. Logging out is in the account menu.'),
]