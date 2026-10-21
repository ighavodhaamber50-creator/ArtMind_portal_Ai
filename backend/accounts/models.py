"""User-related data. Login itself uses Django's built-in User model."""

from types import SimpleNamespace

from django.conf import settings
from django.db import models

from gallery.models import Artwork, Category


class UserPreference(models.Model):
    """Interests a user chose themselves; the recommender mixes these with their activity."""

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='preference')
    favorite_categories = models.ManyToManyField(Category, blank=True)
    favorite_styles = models.JSONField(default=list, blank=True)   # e.g. ["impressionism"]
    favorite_colors = models.JSONField(default=list, blank=True)   # e.g. ["blue", "green"]
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Preferences of {self.user}'


class UserArtwork(models.Model):
    """A painting or picture that a user uploaded to their own private collection."""

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='own_artworks')
    title = models.CharField(max_length=200)
    artist_name = models.CharField(max_length=120, blank=True)  # empty means "the owner's username"
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='+')
    style = models.CharField(max_length=30, choices=Artwork.STYLE_CHOICES)
    medium = models.CharField(max_length=20, choices=Artwork.MEDIUM_CHOICES)
    surface = models.CharField(max_length=20, choices=Artwork.SURFACE_CHOICES, default='canvas')
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='user_artworks/')
    dominant_colors = models.JSONField(default=list, blank=True)  # measured from the image with OpenCV
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.title} ({self.owner})'

    # The PDF and Word builders treat this like a gallery painting, so it provides the
    # same things they ask for: an artist and a list of tags.
    @property
    def artist(self):
        return SimpleNamespace(name=self.artist_name or self.owner.get_username(), nationality='', bio='')

    @property
    def tags(self):
        return []