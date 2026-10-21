"""Serializers: convert gallery models into the JSON the React app receives."""

from rest_framework import serializers

from .models import Artwork, Category
from .services import similar_artworks


class CategorySerializer(serializers.ModelSerializer):
    artwork_count = serializers.IntegerField(read_only=True)  # added by the view

    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'description', 'artwork_count']


class ArtworkListSerializer(serializers.ModelSerializer):
    """Compact version used by gallery cards."""

    artist = serializers.CharField(source='artist.name', read_only=True)
    category = serializers.CharField(source='category.name', read_only=True)
    category_slug = serializers.CharField(source='category.slug', read_only=True)
    style_label = serializers.CharField(source='get_style_display', read_only=True)
    medium_label = serializers.CharField(source='get_medium_display', read_only=True)
    is_favorite = serializers.SerializerMethodField()

    class Meta:
        model = Artwork
        fields = [
            'id', 'title', 'artist', 'category', 'category_slug',
            'style', 'style_label', 'medium', 'medium_label',
            'dominant_colors', 'tags', 'description', 'image',
            'view_count', 'is_favorite',
        ]

    def get_is_favorite(self, obj):
        # The view puts this user's favorite ids in the context (one query, not one per card)
        return obj.id in self.context.get('favorite_ids', set())


class ArtworkDetailSerializer(ArtworkListSerializer):
    """Full version for the painting details page."""

    surface_label = serializers.CharField(source='get_surface_display', read_only=True)
    artist_info = serializers.SerializerMethodField()
    similar_artworks = serializers.SerializerMethodField()

    class Meta(ArtworkListSerializer.Meta):
        fields = ArtworkListSerializer.Meta.fields + [
            'surface', 'surface_label', 'ai_summary', 'artist_info',
            'similar_artworks', 'created_at',
        ]

    def get_artist_info(self, obj):
        return {'name': obj.artist.name, 'nationality': obj.artist.nationality, 'bio': obj.artist.bio}

    def get_similar_artworks(self, obj):
        return ArtworkListSerializer(similar_artworks(obj), many=True, context=self.context).data