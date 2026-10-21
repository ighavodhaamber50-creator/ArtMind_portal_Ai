"""Admin-only statistics. The frontend draws these numbers as charts."""

from collections import Counter
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db.models import Count, Sum
from django.utils import timezone
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from ai_services.models import AIAnalysis, SearchHistory
from gallery.models import Artwork, Category, Favorite, RecentlyViewed

User = get_user_model()
TOP_N = 5


class AnalyticsView(APIView):
    """GET /api/analytics/ (staff only; everyone else gets a 403)."""

    permission_classes = [IsAdminUser]

    def get(self, request):
        week_ago = timezone.now() - timedelta(days=7)
        artworks = list(Artwork.objects.select_related('artist', 'category'))

        most_viewed = [
            {'id': a.id, 'title': a.title, 'artist': a.artist.name,
             'category': a.category.name, 'views': a.view_count}
            for a in Artwork.objects.select_related('artist', 'category').order_by('-view_count')[:TOP_N]
        ]

        popular_categories = [
            {'name': c.name, 'views': c.total_views or 0, 'artworks': c.artwork_count}
            for c in Category.objects.annotate(
                total_views=Sum('artworks__view_count'), artwork_count=Count('artworks'))
            .order_by('-total_views')
        ]

        # Colors are stored in a JSON list, so count them in Python, weighted by views
        color_views = Counter()
        for artwork in artworks:
            for color in artwork.dominant_colors:
                color_views[color] += artwork.view_count
        popular_colors = [{'color': color, 'views': views}
                          for color, views in color_views.most_common(8)]

        searched_categories = list(
            SearchHistory.objects.exclude(category='')
            .values('category').annotate(searches=Count('id')).order_by('-searches')[:TOP_N])

        trending = list(
            RecentlyViewed.objects.filter(viewed_at__gte=week_ago)
            .values('artwork__id', 'artwork__title')
            .annotate(views=Count('id')).order_by('-views')[:TOP_N])
        trending = [{'id': t['artwork__id'], 'title': t['artwork__title'], 'views': t['views']}
                    for t in trending]

        user_activity = {
            'total_users': User.objects.count(),
            'new_users_7d': User.objects.filter(date_joined__gte=week_ago).count(),
            'active_users_7d': RecentlyViewed.objects.filter(viewed_at__gte=week_ago)
                               .values('user').distinct().count(),
            'total_favorites': Favorite.objects.count(),
            'favorites_7d': Favorite.objects.filter(created_at__gte=week_ago).count(),
            'total_artwork_views': sum(a.view_count for a in artworks),
        }

        # Honest reporting: how often real AI was used versus the fallback
        ai_usage = {
            'searches_total': SearchHistory.objects.count(),
            'searches_with_ai': SearchHistory.objects.filter(used_ai=True).count(),
            'analyses_total': AIAnalysis.objects.count(),
            'analyses_real': AIAnalysis.objects.filter(source='computer_vision').count(),
        }

        return Response({
            'totals': {'artworks': len(artworks), 'categories': Category.objects.count()},
            'most_viewed': most_viewed,
            'popular_categories': popular_categories,
            'popular_colors': popular_colors,
            'searched_categories': searched_categories,
            'trending': trending,
            'user_activity': user_activity,
            'ai_usage': ai_usage,
        })