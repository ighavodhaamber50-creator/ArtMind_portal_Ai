"""AI-related endpoints: search, chat, recommendations, and the user dashboard."""

from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from rest_framework.views import APIView

from gallery.models import Favorite, RecentlyViewed
from gallery.serializers import ArtworkListSerializer

from .chatbot import chat, clean_history
from .curation import curated_collections
from .models import SearchHistory
from .nl_search import parse_query, search_artworks
from .recommender import build_profile, recommend

MAX_QUERY_LENGTH = 300
MAX_MESSAGE_LENGTH = 500
MAX_SEARCH_RESULTS = 24


class AiAnonThrottle(AnonRateThrottle):
    """AI calls can cost money, so visitors are limited."""
    rate = '20/min'


class AiUserThrottle(UserRateThrottle):
    rate = '60/min'


def _serialize(artworks, request, favorite_ids, with_reason=False):
    """Turn artworks into JSON; optionally attach the recommender's 'reason' to each."""
    context = {'request': request, 'favorite_ids': favorite_ids}
    data = list(ArtworkListSerializer(artworks, many=True, context=context).data)
    if with_reason:
        for item, artwork in zip(data, artworks):
            item['reason'] = artwork.reason
    return data


def _favorite_ids(user):
    if not user.is_authenticated:
        return set()
    return set(Favorite.objects.filter(user=user).values_list('artwork_id', flat=True))


class SearchView(APIView):
    """POST /api/search/ with {"query": "watercolor landscape paintings"}"""

    permission_classes = [AllowAny]
    throttle_classes = [AiAnonThrottle, AiUserThrottle]

    def post(self, request):
        query = request.data.get('query', '')
        if not isinstance(query, str) or not query.strip():
            return Response({'detail': 'Please type what you are looking for.'},
                            status=status.HTTP_400_BAD_REQUEST)
        query = query.strip()
        if len(query) > MAX_QUERY_LENGTH:
            return Response({'detail': f'Please keep your search under {MAX_QUERY_LENGTH} characters.'},
                            status=status.HTTP_400_BAD_REQUEST)

        criteria, used_ai, note = parse_query(query)
        artworks, relaxed = search_artworks(criteria)
        artworks = artworks[:MAX_SEARCH_RESULTS]

        SearchHistory.objects.create(
            user=request.user if request.user.is_authenticated else None,
            query=query, category=criteria['category'] or '', criteria=criteria,
            used_ai=used_ai, results_count=len(artworks))

        if not artworks:
            message = ('No paintings matched that search. Try a category, color or medium, '
                       'for example "blue watercolor landscape".')
        elif relaxed:
            message = 'No exact match, so these are the closest paintings.'
        else:
            message = ''

        return Response({
            'query': query,
            'engine': 'openai' if used_ai else 'keyword-fallback',
            'used_ai': used_ai,
            'note': note,
            'message': message,
            'relaxed': relaxed,
            'criteria': criteria,
            'count': len(artworks),
            'results': _serialize(artworks, request, _favorite_ids(request.user)),
        })


class ChatView(APIView):
    """POST /api/ai/chat/ with {"message": "What is impressionism?", "history": [...]}"""

    permission_classes = [AllowAny]
    throttle_classes = [AiAnonThrottle, AiUserThrottle]

    def post(self, request):
        message = request.data.get('message', '')
        if not isinstance(message, str) or not message.strip():
            return Response({'detail': 'Please type a question for the assistant.'},
                            status=status.HTTP_400_BAD_REQUEST)
        message = message.strip()
        if len(message) > MAX_MESSAGE_LENGTH:
            return Response({'detail': f'Please keep your message under {MAX_MESSAGE_LENGTH} characters.'},
                            status=status.HTTP_400_BAD_REQUEST)

        result = chat(message, clean_history(request.data.get('history')))
        return Response({
            'reply': result['reply'],
            'engine': 'openai' if result['used_ai'] else 'built-in',
            'used_ai': result['used_ai'],
            'note': result['note'],
            'artworks': _serialize(result['artworks'], request, _favorite_ids(request.user)),
            'suggestions': result['suggestions'],
        })


class RecommendationView(APIView):
    """GET /api/recommendations/?limit=8  ('Recommended For You')"""

    permission_classes = [AllowAny]  # visitors get popular paintings, users get personalized ones

    def get(self, request):
        try:
            limit = min(max(int(request.query_params.get('limit', 8)), 1), 24)
        except ValueError:
            limit = 8

        artworks, personalized = recommend(request.user, limit)
        return Response({
            'personalized': personalized,
            'results': _serialize(artworks, request, _favorite_ids(request.user), with_reason=True),
        })


class DashboardView(APIView):
    """GET /api/dashboard/ : everything the personalized page needs, in one request."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        profile = build_profile(user)
        favorite_ids = profile['favorite_ids']

        recent_qs = (RecentlyViewed.objects.filter(user=user)
                     .select_related('artwork__artist', 'artwork__category'))
        recent = [view.artwork for view in recent_qs[:8]]

        favorites = [fav.artwork for fav in
                     Favorite.objects.filter(user=user)
                     .select_related('artwork__artist', 'artwork__category')]

        recommended, personalized = recommend(user, 6)

        # "Favorite Categories": the weighted counts, turned into percentages for a chart
        total = sum(profile['categories'].values())
        favorite_categories = [
            {'name': name, 'points': points, 'percent': round(100 * points / total) if total else 0}
            for name, points in profile['categories'].most_common(5)
        ]

        collections = [
            {'title': c['title'], 'description': c['description'],
             'artworks': _serialize(c['artworks'], request, favorite_ids)}
            for c in curated_collections(profile)
        ]

        return Response({
            'user': {'username': user.username},
            'stats': {'favorites': len(favorites), 'recently_viewed': recent_qs.count()},
            'recently_viewed': _serialize(recent, request, favorite_ids),
            'favorites': _serialize(favorites, request, favorite_ids),
            'favorite_categories': favorite_categories,
            'personalized': personalized,
            'recommendations': _serialize(recommended, request, favorite_ids, with_reason=True),
            'collections': collections,
        })