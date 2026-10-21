"""AI-curated collections: themed groups of paintings built from a user's taste profile."""

from gallery.models import Artwork

COLLECTION_SIZE = 4
STYLE_LABELS = dict(Artwork.STYLE_CHOICES)


def curated_collections(profile):
    """Return up to three collections: [{'title', 'description', 'artworks': [Artwork, ...]}]."""
    if not profile['has_activity']:
        return []  # nothing to base a collection on yet

    # Paintings the user has not saved yet, most popular first
    candidates = list(
        Artwork.objects.select_related('artist', 'category')
        .exclude(id__in=profile['favorite_ids'])
        .order_by('-view_count', 'title'))

    top_categories = [name for name, _ in profile['categories'].most_common(2)]
    top_styles = [code for code, _ in profile['styles'].most_common(1)]
    top_colors = [color for color, _ in profile['colors'].most_common(1)]

    collections = []

    def add(title, description, artworks):
        if len(artworks) >= 2:  # a collection of one painting looks thin
            collections.append({'title': title, 'description': description,
                                'artworks': artworks[:COLLECTION_SIZE]})

    # 1. Favorite category in favorite color, e.g. "Your Love for Blue Landscape Paintings"
    if top_colors:
        color = top_colors[0]
        in_color = [a for a in candidates if color in a.dominant_colors]
        in_category = [a for a in in_color
                       if top_categories and a.category.name == top_categories[0]]
        if len(in_category) >= 2:
            add(f'Your Love for {color.title()} {top_categories[0]} Paintings',
                f'{top_categories[0]} works in the {color} tones you keep coming back to.',
                in_category)
        else:
            add(f'Your Love for {color.title()} Tones',
                f'Paintings rich in {color}, a color you often choose.', in_color)

    # 2. A category you like, e.g. "Abstract Art You May Like" (your second favorite if you have one)
    if top_categories:
        category = top_categories[-1]
        add(f'{category} Art You May Like',
            f'More {category.lower()} paintings picked from your activity.',
            [a for a in candidates if a.category.name == category])

    # 3. Your favorite artistic style
    if top_styles:
        label = STYLE_LABELS.get(top_styles[0], top_styles[0].title())
        add(f'Explore {label}', f'Paintings in the {label} style you respond to.',
            [a for a in candidates if a.style == top_styles[0]])

    return collections