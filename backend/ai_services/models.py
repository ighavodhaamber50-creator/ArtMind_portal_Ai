"""Records of searches and image analyses, used for analytics and history."""

from django.conf import settings
from django.db import models

from gallery.models import Artwork


class SearchHistory(models.Model):
    """One search. Anonymous visitors are allowed (user stays empty)."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                             on_delete=models.SET_NULL, related_name='searches')
    query = models.CharField(max_length=300)
    category = models.CharField(max_length=60, blank=True)   # kept separate so analytics can count it
    criteria = models.JSONField(default=dict, blank=True)    # extracted style, medium, color, theme
    used_ai = models.BooleanField(default=False)             # False = keyword fallback was used
    results_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'search history'

    def __str__(self):
        return self.query


class AIAnalysis(models.Model):
    """Result of analyzing an uploaded painting image."""

    SOURCE_CHOICES = [
        ('computer_vision', 'Real image analysis'),
        ('fallback', 'Fallback / demo result'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                             on_delete=models.SET_NULL, related_name='analyses')
    image = models.ImageField(upload_to='uploads/analysis/')
    predicted_category = models.CharField(max_length=60, blank=True)
    predicted_style = models.CharField(max_length=30, blank=True)
    dominant_colors = models.JSONField(default=list, blank=True)
    similar_artworks = models.ManyToManyField(Artwork, blank=True)
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default='fallback')
    notes = models.TextField(blank=True)  # e.g. why a fallback was used
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'AI analyses'

    def __str__(self):
        return f'Analysis #{self.pk} ({self.source})'