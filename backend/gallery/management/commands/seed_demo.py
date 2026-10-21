"""Create a demo account with some activity, so My Collection and Analytics look alive in a demo.

Safe to run more than once. Run seed_gallery first. The password below is for local demos only.
"""

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from accounts.models import UserPreference
from ai_services.models import SearchHistory
from gallery.models import Artwork, Category, Favorite, RecentlyViewed

DEMO_USERNAME = 'demo'
DEMO_PASSWORD = 'ArtMind#Demo2026'

FAVORITES = ['Harbour at First Light', 'Late Summer Sunflowers', 'Valley After Rain']
VIEWED = ['Blue Resonance', 'Midnight Currents', 'Savannah Dusk', 'Lavender Field Study', 'Forest Mirror']
SEARCHES = [
    ('blue watercolor landscape', 'Landscape'),
    ('oil paintings with nature themes', 'Nature'),
    ('modern abstract paintings with blue colors', 'Abstract'),
    ('sunset by the sea', ''),
    ('flower paintings', 'Flower'),
    ('abstract', 'Abstract'),
]


class Command(BaseCommand):
    help = 'Create the demo user with favorites, viewed paintings, preferences and search history.'

    def handle(self, *args, **options):
        if not Artwork.objects.exists():
            raise CommandError('There are no paintings yet. Run "python manage.py seed_gallery" first.')

        User = get_user_model()
        user, _ = User.objects.get_or_create(username=DEMO_USERNAME, defaults={'email': 'demo@example.com'})
        user.set_password(DEMO_PASSWORD)
        user.save()

        for title in FAVORITES:
            artwork = Artwork.objects.filter(title=title).first()
            if artwork:
                Favorite.objects.get_or_create(user=user, artwork=artwork)

        for title in VIEWED:  # the last one in the list counts as the newest view
            artwork = Artwork.objects.filter(title=title).first()
            if artwork:
                RecentlyViewed.objects.get_or_create(user=user, artwork=artwork)

        preference, _ = UserPreference.objects.get_or_create(user=user)
        preference.favorite_styles = ['impressionism']
        preference.favorite_colors = ['blue', 'green']
        preference.save()
        preference.favorite_categories.set(Category.objects.filter(name__in=['Landscape', 'Flower']))

        if not SearchHistory.objects.filter(user=user).exists():
            for query, category in SEARCHES:
                SearchHistory.objects.create(
                    user=user, query=query, category=category, used_ai=False, results_count=1)

        self.stdout.write(self.style.SUCCESS(f'Demo user ready: {DEMO_USERNAME} / {DEMO_PASSWORD}'))