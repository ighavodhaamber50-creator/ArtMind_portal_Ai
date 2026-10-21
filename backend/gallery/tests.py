"""Tests for the gallery API: listing, filtering, sorting, details, and favorites."""

from rest_framework.test import APITestCase

from .factories import make_artwork, make_user
from .models import Favorite, RecentlyViewed


class GalleryApiTests(APITestCase):
    def setUp(self):
        self.harbour = make_artwork('Harbour Test', 'Landscape', 'impressionism', 'oil',
                                    ['blue', 'yellow'], ['sea'], views=50)
        self.blue = make_artwork('Blue Test', 'Abstract', 'abstract', 'acrylic', ['blue'], [], views=5)
        self.rose = make_artwork('Rose Test', 'Flower', 'realism', 'watercolor', ['pink'], ['rose'], views=20)

    def titles(self, response):
        return [item['title'] for item in response.data['results']]

    def test_list_is_paginated_and_complete(self):
        response = self.client.get('/api/artworks/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 3)

    def test_filter_by_category_slug(self):
        response = self.client.get('/api/artworks/?category=landscape')
        self.assertEqual(self.titles(response), ['Harbour Test'])

    def test_filter_by_color_looks_inside_the_color_list(self):
        response = self.client.get('/api/artworks/?color=blue')
        self.assertEqual(set(self.titles(response)), {'Harbour Test', 'Blue Test'})

    def test_filter_by_medium_and_style(self):
        self.assertEqual(self.titles(self.client.get('/api/artworks/?medium=watercolor')), ['Rose Test'])
        self.assertEqual(self.titles(self.client.get('/api/artworks/?style=abstract')), ['Blue Test'])

    def test_sorting(self):
        popular = self.client.get('/api/artworks/?sort=popular')
        self.assertEqual(self.titles(popular), ['Harbour Test', 'Rose Test', 'Blue Test'])
        alphabetical = self.client.get('/api/artworks/?sort=alphabetical')
        self.assertEqual(self.titles(alphabetical), ['Blue Test', 'Harbour Test', 'Rose Test'])

    def test_categories_endpoint_counts_paintings(self):
        response = self.client.get('/api/categories/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual({c['name'] for c in response.data}, {'Landscape', 'Abstract', 'Flower'})
        self.assertTrue(all(c['artwork_count'] == 1 for c in response.data))

    def test_detail_counts_one_view_each_time(self):
        url = f'/api/artworks/{self.harbour.id}/'
        first = self.client.get(url)
        self.assertEqual(first.status_code, 200)
        self.assertEqual(first.data['view_count'], 51)
        self.assertEqual(self.client.get(url).data['view_count'], 52)
        self.assertEqual(first.data['artist_info']['name'], 'Pat Tester')
        self.assertIn('similar_artworks', first.data)

    def test_missing_painting_gives_a_friendly_404(self):
        response = self.client.get('/api/artworks/9999/')
        self.assertEqual(response.status_code, 404)
        self.assertIn('detail', response.data)

    def test_detail_records_recently_viewed_for_logged_in_users(self):
        user = make_user()
        self.client.force_authenticate(user)
        self.client.get(f'/api/artworks/{self.rose.id}/')
        self.assertTrue(RecentlyViewed.objects.filter(user=user, artwork=self.rose).exists())


class FavoriteTests(APITestCase):
    def setUp(self):
        self.user = make_user()
        self.art = make_artwork('Harbour Test')

    def test_favorites_need_a_login(self):
        self.assertEqual(self.client.get('/api/favorites/').status_code, 403)
        response = self.client.post('/api/favorites/', {'artwork_id': self.art.id}, format='json')
        self.assertEqual(response.status_code, 403)

    def test_add_list_and_remove(self):
        self.client.force_authenticate(self.user)
        payload = {'artwork_id': self.art.id}

        self.assertEqual(self.client.post('/api/favorites/', payload, format='json').status_code, 201)
        self.assertEqual(self.client.post('/api/favorites/', payload, format='json').status_code, 200)
        self.assertEqual(Favorite.objects.filter(user=self.user).count(), 1)  # no duplicates

        listing = self.client.get('/api/favorites/')
        self.assertEqual([item['title'] for item in listing.data], ['Harbour Test'])
        self.assertTrue(listing.data[0]['is_favorite'])

        self.assertEqual(self.client.delete(f'/api/favorites/{self.art.id}/').status_code, 204)
        self.assertEqual(self.client.delete(f'/api/favorites/{self.art.id}/').status_code, 404)

    def test_bad_input_gets_friendly_errors(self):
        self.client.force_authenticate(self.user)
        missing = self.client.post('/api/favorites/', {'artwork_id': 9999}, format='json')
        self.assertEqual(missing.status_code, 404)
        not_a_number = self.client.post('/api/favorites/', {'artwork_id': 'abc'}, format='json')
        self.assertEqual(not_a_number.status_code, 400)