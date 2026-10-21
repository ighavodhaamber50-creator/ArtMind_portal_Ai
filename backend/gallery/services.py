"""Reusable gallery logic, kept separate from the views."""

from .models import Artwork


def similar_artworks(artwork, limit=4):
    """Rank other paintings by how much they resemble this one.

    Same category is worth 3 points, same style 2 points, and each shared
    dominant color 1 point. Ties are broken by popularity.
    """
    candidates = Artwork.objects.exclude(pk=artwork.pk).select_related('artist', 'category')
    colors = set(artwork.dominant_colors)

    def score(other):
        points = 0
        if other.category_id == artwork.category_id:
            points += 3
        if other.style == artwork.style:
            points += 2
        return points + len(colors & set(other.dominant_colors))

    ranked = sorted(candidates, key=lambda a: (score(a), a.view_count), reverse=True)
    return ranked[:limit]