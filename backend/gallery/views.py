"""Read-only gallery endpoints: categories, artwork list, artwork detail."""

from datetime import timedelta

from django.db.models import Count, F, Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Artwork, Category, Favorite, RecentlyViewed
from .serializers import ArtworkDetailSerializer, ArtworkListSerializer, CategorySerializer


class ArtworkPagination(PageNumberPagination):
    page_size = 12
    page_size_query_param = 'page_size'
    max_page_size = 50


class FavoriteContextMixin:
    """Gives serializers the set of artwork ids the current user has favorited."""

    def get_serializer_context(self):
        context = super().get_serializer_context()
        user = self.request.user
        if user.is_authenticated:
            context['favorite_ids'] = set(
                Favorite.objects.filter(user=user).values_list('artwork_id', flat=True))
        else:
            context['favorite_ids'] = set()
        return context


class CategoryListView(ListAPIView):
    serializer_class = CategorySerializer
    pagination_class = None  # only six categories, so no pages needed

    def get_queryset(self):
        return Category.objects.annotate(artwork_count=Count('artworks'))


class ArtworkListView(FavoriteContextMixin, ListAPIView):
    """Supports ?category=<slug> &style= &medium= &color= &sort=popular|recent|alphabetical|trending"""

    serializer_class = ArtworkListSerializer
    pagination_class = ArtworkPagination

    def get_queryset(self):
        params = self.request.query_params
        queryset = Artwork.objects.select_related('artist', 'category')

        if params.get('category'):
            queryset = queryset.filter(category__slug=params['category'])
        if params.get('style'):
            queryset = queryset.filter(style=params['style'])
        if params.get('medium'):
            queryset = queryset.filter(medium=params['medium'])
        if params.get('color'):
            # Colors live in a JSON list; SQLite can't search inside it, so match in Python.
            wanted = params['color'].lower()
            ids = [pk for pk, colors in Artwork.objects.values_list('id', 'dominant_colors')
                   if wanted in colors]
            queryset = queryset.filter(id__in=ids)

        sort = params.get('sort', 'recent')
        if sort == 'popular':
            return queryset.order_by('-view_count', 'title')
        if sort == 'alphabetical':
            return queryset.order_by('title')
        if sort == 'trending':
            # Trending = most views in the last 7 days, then overall popularity
            week_ago = timezone.now() - timedelta(days=7)
            return queryset.annotate(
                recent_views=Count('views', filter=Q(views__viewed_at__gte=week_ago))
            ).order_by('-recent_views', '-view_count')
        return queryset.order_by('-created_at', '-id')


class ArtworkDetailView(FavoriteContextMixin, RetrieveAPIView):
    queryset = Artwork.objects.select_related('artist', 'category')
    serializer_class = ArtworkDetailSerializer

    def retrieve(self, request, *args, **kwargs):
        artwork = self.get_object()  # a missing id gives a 404 automatically

        # Count the view (F() lets the database do the +1 safely)
        Artwork.objects.filter(pk=artwork.pk).update(view_count=F('view_count') + 1)

        # Logged-in users also get it in their "recently viewed" list
        if request.user.is_authenticated:
            record, created = RecentlyViewed.objects.get_or_create(user=request.user, artwork=artwork)
            if not created:
                record.save()  # refreshes viewed_at

        artwork.refresh_from_db()
        return Response(self.get_serializer(artwork).data)



class FavoriteListView(APIView):
    """GET lists the user's favorites; POST adds one."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        favorites = (Favorite.objects.filter(user=request.user)
                     .select_related('artwork__artist', 'artwork__category'))
        artworks = [favorite.artwork for favorite in favorites]
        context = {'request': request, 'favorite_ids': {a.id for a in artworks}}
        return Response(ArtworkListSerializer(artworks, many=True, context=context).data)

    def post(self, request):
        try:
            artwork_id = int(request.data.get('artwork_id'))
        except (TypeError, ValueError):
            return Response({'detail': 'artwork_id is required and must be a number.'},
                            status=status.HTTP_400_BAD_REQUEST)

        artwork = get_object_or_404(Artwork, pk=artwork_id)  # 404 if the painting doesn't exist
        favorite, created = Favorite.objects.get_or_create(user=request.user, artwork=artwork)
        return Response(
            {'detail': 'Added to favorites.' if created else 'Already in favorites.',
             'artwork_id': artwork.id, 'is_favorite': True},
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


class FavoriteDetailView(APIView):
    """DELETE removes one favorite, identified by the artwork's id."""

    permission_classes = [IsAuthenticated]

    def delete(self, request, artwork_id):
        deleted, _ = Favorite.objects.filter(user=request.user, artwork_id=artwork_id).delete()
        if not deleted:
            return Response({'detail': 'That artwork is not in your favorites.'},
                            status=status.HTTP_404_NOT_FOUND)
        return Response(status=status.HTTP_204_NO_CONTENT)