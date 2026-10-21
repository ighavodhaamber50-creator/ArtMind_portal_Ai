"""Tests for the admin-only analytics endpoint."""

from rest_framework.test import APITestCase

from ai_services.models import SearchHistory
from gallery.factories import make_artwork, make_user


class AnalyticsTests(APITestCase):
    def setUp(self):
        make_artwork('Harbour Test', 'Landscape', 'impressionism', 'oil', ['blue', 'yellow'], views=50)
        make_artwork('Blue Test', 'Abstract', 'abstract', 'acrylic', ['blue'], views=5)

    def test_visitors_and_ordinary_users_are_refused(self):
        self.assertEqual(self.client.get('/api/analytics/').status_code, 403)
        self.client.force_authenticate(make_user('viewer'))
        self.assertEqual(self.client.get('/api/analytics/').status_code, 403)

    def test_staff_see_the_numbers(self):
        SearchHistory.objects.create(query='x', category='Landscape', used_ai=False, results_count=1)
        self.client.force_authenticate(make_user('boss', is_staff=True))

        response = self.client.get('/api/analytics/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['most_viewed'][0]['title'], 'Harbour Test')
        self.assertEqual(response.data['totals']['artworks'], 2)
        self.assertEqual(response.data['user_activity']['total_users'], 1)
        self.assertEqual(response.data['popular_colors'][0]['color'], 'blue')
        self.assertEqual(response.data['searched_categories'][0]['category'], 'Landscape')
        self.assertEqual(response.data['ai_usage']['searches_total'], 1)
        self.assertEqual(response.data['ai_usage']['searches_with_ai'], 0)