"""Helpers that build small sample data sets for the automated tests."""

from django.contrib.auth import get_user_model

from .models import Artist, Artwork, Category

TEST_PASSWORD = 'ArtMind#Test2026'


def make_user(username='tester', **extra):
    return get_user_model().objects.create_user(username=username, password=TEST_PASSWORD, **extra)


def make_artwork(title, category='Landscape', style='impressionism', medium='oil',
                 colors=None, tags=None, views=10, artist='Pat Tester'):
    category_obj, _ = Category.objects.get_or_create(
        name=category, defaults={'slug': category.lower(), 'description': f'{category} test category.'})
    artist_obj, _ = Artist.objects.get_or_create(
        name=artist, defaults={'nationality': 'Testland', 'bio': 'A painter who exists only in tests.'})
    return Artwork.objects.create(
        title=title, artist=artist_obj, category=category_obj, style=style, medium=medium,
        surface='canvas', description=f'{title} is a test painting.',
        dominant_colors=colors or [], tags=tags or [], view_count=views)