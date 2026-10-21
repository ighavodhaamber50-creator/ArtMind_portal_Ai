"""Rule-based recommendation engine (no external AI needed).

Learns what a user likes from their favorites, recently viewed paintings and saved
preferences, then scores every other painting against that taste profile.
Kept separate from the views so it can be swapped for a smarter model later.
"""

from collections import Counter
from datetime import timedelta

from django.db.models import Count
from django.utils import timezone

from accounts.models import UserPreference
from gallery.models import Artwork, Favorite, RecentlyViewed

FAVORITE_WEIGHT = 3    # saving a painting is the strongest signal
PREFERENCE_WEIGHT = 2  # interests the user chose themselves
VIEW_WEIGHT = 1        # opening a painting is a weaker signal


def build_profile(user):
    """Count how much a user likes each category, style and color.

    Also reused by the dashboard (favorite categories, AI-curated collections).
    """
    categories, styles, colors = Counter(), Counter(), Counter()
    favorite_ids, viewed_ids = set(), set()

    def add(artwork, weight):
        categories[artwork.category.name] += weight
        styles[artwork.style] += weight
        for color in artwork.dominant_colors:
            colors[color] += weight

    for favorite in Favorite.objects.filter(user=user).select_related('artwork__category'):
        favorite_ids.add(favorite.artwork_id)
        add(favorite.artwork, FAVORITE_WEIGHT)

    for view in RecentlyViewed.objects.filter(user=user).select_related('artwork__category')[:20]:
        viewed_ids.add(view.artwork_id)
        add(view.artwork, VIEW_WEIGHT)

    preference = UserPreference.objects.filter(user=user).first()
    if preference:
        for category in preference.favorite_categories.all():
            categories[category.name] += PREFERENCE_WEIGHT
        for style in preference.favorite_styles:
            styles[style] += PREFERENCE_WEIGHT
        for color in preference.favorite_colors:
            colors[color] += PREFERENCE_WEIGHT

    return {
        'categories': categories, 'styles': styles, 'colors': colors,
        'favorite_ids': favorite_ids, 'viewed_ids': viewed_ids,
        'has_activity': bool(categories or styles or colors),
    }


def _popularity_scores(artworks):
    """Give each painting two 0-1 scores: overall popularity and last-7-days trending."""
    week_ago = timezone.now() - timedelta(days=7)
    recent = dict(
        RecentlyViewed.objects.filter(viewed_at__gte=week_ago)
        .values('artwork_id').annotate(n=Count('id')).values_list('artwork_id', 'n'))
    max_views = max((a.view_count for a in artworks), default=1) or 1
    max_recent = max(recent.values(), default=1)
    return {a.id: (a.view_count / max_views, recent.get(a.id, 0) / max_recent) for a in artworks}


def recommend(user, limit=8):
    """Return (artworks, personalized). Each artwork gets a .reason string explaining the pick."""
    artworks = list(Artwork.objects.select_related('artist', 'category'))
    popularity = _popularity_scores(artworks)

    profile = build_profile(user) if user.is_authenticated else None
    personalized = bool(profile and profile['has_activity'])

    scored = []
    for art in artworks:
        if personalized and art.id in profile['favorite_ids']:
            continue  # no point recommending what they already saved

        popular, trending = popularity[art.id]
        score = popular + trending
        reasons = []

        if personalized:
            category_points = profile['categories'].get(art.category.name, 0)
            style_points = profile['styles'].get(art.style, 0)
            shared_colors = [c for c in art.dominant_colors if profile['colors'].get(c)]

            score += category_points * 2 + style_points * 1.5
            score += sum(profile['colors'][c] for c in shared_colors) * 0.5
            if art.id in profile['viewed_ids']:
                score -= 2  # already seen it, so favor fresh paintings

            if category_points:
                reasons.append(f'You enjoy {art.category.name} paintings')
            if style_points:
                reasons.append(f'Matches your taste for {art.get_style_display()}')
            if shared_colors:
                reasons.append('Uses colors you like: ' + ', '.join(shared_colors[:2]))

        if not reasons:
            reasons.append('Trending this week' if trending > 0.5 else 'Popular with visitors')

        art.reason = ' · '.join(reasons[:2])
        scored.append((score, art))

    scored.sort(key=lambda pair: (pair[0], pair[1].view_count), reverse=True)
    return [art for _, art in scored[:limit]], personalized