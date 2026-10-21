"""Database models for the gallery: categories, artists, artworks, and user activity."""

from django.conf import settings
from django.db import models


class Category(models.Model):
    """A broad grouping such as Abstract, Landscape, or Flower."""

    name = models.CharField(max_length=60, unique=True)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = 'categories'
        ordering = ['name']

    def __str__(self):
        return self.name


class Artist(models.Model):
    name = models.CharField(max_length=120, unique=True)
    nationality = models.CharField(max_length=80, blank=True)
    bio = models.TextField(blank=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Artwork(models.Model):
    """One painting. Style, medium, and colors are used for filtering and recommendations."""

    MEDIUM_CHOICES = [
        ('oil', 'Oil'),
        ('watercolor', 'Watercolor'),
        ('acrylic', 'Acrylic'),
        ('pastel', 'Pastel'),
        ('ink', 'Ink'),
        ('mixed', 'Mixed Media'),
    ]
    SURFACE_CHOICES = [
        ('canvas', 'Canvas'),
        ('paper', 'Paper'),
        ('wood', 'Wood Panel'),
        ('board', 'Board'),
    ]
    STYLE_CHOICES = [
        ('impressionism', 'Impressionism'),
        ('expressionism', 'Expressionism'),
        ('abstract', 'Abstract'),
        ('realism', 'Realism'),
        ('surrealism', 'Surrealism'),
        ('modern', 'Modern'),
        ('classical', 'Classical'),
        ('contemporary', 'Contemporary'),
    ]

    title = models.CharField(max_length=200)
    artist = models.ForeignKey(Artist, on_delete=models.PROTECT, related_name='artworks')
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='artworks')
    style = models.CharField(max_length=30, choices=STYLE_CHOICES)
    medium = models.CharField(max_length=20, choices=MEDIUM_CHOICES)
    surface = models.CharField(max_length=20, choices=SURFACE_CHOICES, default='canvas')
    description = models.TextField()
    ai_summary = models.TextField(blank=True)  # filled in by the AI service later
    dominant_colors = models.JSONField(default=list, blank=True)  # e.g. ["blue", "green"]
    tags = models.JSONField(default=list, blank=True)  # e.g. ["sea", "sunset"]
    image = models.ImageField(upload_to='artworks/')
    view_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.title} by {self.artist}'


class Favorite(models.Model):
    """A user saving an artwork. One row per user and artwork."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='favorites')
    artwork = models.ForeignKey(Artwork, on_delete=models.CASCADE, related_name='favorited_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'artwork'], name='unique_favorite'),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user} likes {self.artwork}'


class RecentlyViewed(models.Model):
    """Last time a user opened an artwork. Re-opening updates viewed_at instead of adding a row."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='recently_viewed')
    artwork = models.ForeignKey(Artwork, on_delete=models.CASCADE, related_name='views')
    viewed_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'artwork'], name='unique_recent_view'),
        ]
        ordering = ['-viewed_at']
        verbose_name_plural = 'recently viewed'

    def __str__(self):
        return f'{self.user} viewed {self.artwork}'