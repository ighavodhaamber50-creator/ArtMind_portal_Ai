"""Serializers for accounts: registration, the logged-in user, and the user's own artworks."""

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from ai_services.serializers import ImageUploadSerializer
from gallery.models import Artwork, Category

from .models import UserArtwork

User = get_user_model()


def user_payload(user):
    """The small bit of user info the frontend needs. Never includes the password."""
    return {
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'is_staff': user.is_staff,  # lets the frontend show the admin dashboard link
    }


class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField(required=False, allow_blank=True)
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})

    def validate_username(self, value):
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError('That username is already taken.')
        return value

    def validate(self, data):
        # Run Django's built-in password rules (length, too common, all numeric, too similar)
        candidate = User(username=data['username'], email=data.get('email', ''))
        try:
            validate_password(data['password'], candidate)
        except DjangoValidationError as exc:
            raise serializers.ValidationError({'password': list(exc.messages)})
        return data


class UserArtworkSerializer(serializers.ModelSerializer):
    """How one of the user's own paintings is sent to the frontend (read only)."""

    artist = serializers.CharField(source='artist.name', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    category_slug = serializers.CharField(source='category.slug', read_only=True)
    style_label = serializers.CharField(source='get_style_display', read_only=True)
    medium_label = serializers.CharField(source='get_medium_display', read_only=True)
    surface_label = serializers.CharField(source='get_surface_display', read_only=True)

    class Meta:
        model = UserArtwork
        fields = [
            'id', 'title', 'artist', 'artist_name', 'category', 'category_name', 'category_slug',
            'style', 'style_label', 'medium', 'medium_label', 'surface', 'surface_label',
            'description', 'image', 'dominant_colors', 'created_at',
        ]
        read_only_fields = fields


class UserArtworkInputSerializer(ImageUploadSerializer):
    """What a user fills in to add a painting. The image checks come from ImageUploadSerializer."""

    title = serializers.CharField(max_length=200)
    artist_name = serializers.CharField(max_length=120, required=False, allow_blank=True)
    category = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        error_messages={'required': 'Please choose a category.',
                        'does_not_exist': 'That category does not exist.',
                        'incorrect_type': 'Please choose a category.'})
    style = serializers.ChoiceField(choices=Artwork.STYLE_CHOICES)
    medium = serializers.ChoiceField(choices=Artwork.MEDIUM_CHOICES)
    surface = serializers.ChoiceField(choices=Artwork.SURFACE_CHOICES, required=False, default='canvas')
    description = serializers.CharField(max_length=2000, required=False, allow_blank=True)