"""Tests for search, the assistant, recommendations, image analysis, summaries, downloads and the dashboard.

AI is switched off (no key) in every test, so results are predictable and nothing is sent to OpenAI.
Uploaded files go to a temporary folder that is deleted afterwards.
"""

import shutil
import tempfile
from io import BytesIO

from django.contrib.auth.models import AnonymousUser
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from PIL import Image
from rest_framework.test import APITestCase

from gallery.factories import make_artwork, make_user
from gallery.models import Favorite

from .models import AIAnalysis, SearchHistory
from .nl_search import extract_with_keywords, get_vocabulary
from .recommender import recommend

TEMP_MEDIA = tempfile.mkdtemp()


def sample_png():
    """A small four-colour picture with a little noise, built in memory."""
    palette = [(40, 90, 170), (235, 200, 70), (50, 130, 80), (240, 240, 235)]
    image = Image.new('RGB', (64, 64))
    pixels = image.load()
    for x in range(64):
        for y in range(64):
            base = palette[(x // 16 + y // 16) % 4]
            pixels[x, y] = tuple(min(255, channel + (x * y) % 7) for channel in base)
    buffer = BytesIO()
    image.save(buffer, 'PNG')
    return SimpleUploadedFile('sample.png', buffer.getvalue(), content_type='image/png')


@override_settings(OPENAI_API_KEY='')
class SearchTests(APITestCase):
    def setUp(self):
        cache.clear()  # the AI endpoints are rate limited, so start every test fresh
        make_artwork('Forest Mirror', 'Nature', 'realism', 'oil', ['green'], ['forest'])
        make_artwork('Valley After Rain', 'Landscape', 'realism', 'watercolor', ['green', 'blue'], ['valley'])
        make_artwork('Midnight Currents', 'Abstract', 'modern', 'mixed', ['blue', 'purple'], ['night'])

    def search(self, text):
        return self.client.post('/api/search/', {'query': text}, format='json')

    def test_oil_paintings_with_nature_themes(self):
        response = self.search('Show me oil paintings with nature themes.')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['criteria']['category'], 'Nature')
        self.assertEqual(response.data['criteria']['medium'], 'oil')
        self.assertEqual([a['title'] for a in response.data['results']], ['Forest Mirror'])
        self.assertFalse(response.data['used_ai'])
        self.assertEqual(response.data['engine'], 'keyword-fallback')

    def test_modern_abstract_paintings_with_blue(self):
        response = self.search('Show me modern abstract paintings with blue colors.')
        criteria = response.data['criteria']
        self.assertEqual((criteria['category'], criteria['style'], criteria['colors']),
                         ('Abstract', 'modern', ['blue']))
        self.assertEqual([a['title'] for a in response.data['results']], ['Midnight Currents'])

    def test_typos_are_forgiven(self):
        response = self.search('show me abstracy paintings')
        self.assertEqual(response.data['criteria']['category'], 'Abstract')
        helper = extract_with_keywords('landscap paintings', get_vocabulary())
        self.assertEqual(helper['category'], 'Landscape')

    def test_nothing_found_is_a_friendly_answer_not_an_error(self):
        response = self.search('unicorns')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 0)
        self.assertTrue(response.data['message'])

    def test_empty_search_is_rejected(self):
        self.assertEqual(self.search('   ').status_code, 400)

    def test_every_search_is_logged(self):
        self.search('Show me oil paintings with nature themes.')
        entry = SearchHistory.objects.get()
        self.assertEqual(entry.category, 'Nature')
        self.assertFalse(entry.used_ai)


@override_settings(OPENAI_API_KEY='')
class ChatTests(APITestCase):
    def setUp(self):
        cache.clear()
        make_artwork('Harbour Test', 'Landscape', 'impressionism', 'oil', ['blue', 'yellow', 'green'])
        make_artwork('Midnight Currents', 'Abstract', 'modern', 'mixed', ['blue', 'purple'])
        make_artwork('Chapel Test', 'Religious', 'classical', 'oil', ['gold'], artist='Elena Marwood')

    def ask(self, message):
        return self.client.post('/api/ai/chat/', {'message': message}, format='json')

    def test_explains_a_style(self):
        response = self.ask('What is impressionism?')
        self.assertEqual(response.status_code, 200)
        self.assertIn('Impressionism', response.data['reply'])
        self.assertEqual(response.data['artworks'], [])
        self.assertFalse(response.data['used_ai'])
        self.assertEqual(response.data['engine'], 'built-in')

    def test_compares_two_mediums(self):
        response = self.ask('What is the difference between watercolor and oil painting?')
        self.assertIn('Watercolor', response.data['reply'])
        self.assertIn('Oil', response.data['reply'])

    def test_recommends_paintings_from_the_gallery(self):
        response = self.ask('Recommend some landscape paintings')
        self.assertEqual([a['title'] for a in response.data['artworks']], ['Harbour Test'])

    def test_long_forms_and_typos_still_find_paintings(self):
        # This exact sentence once returned the "My Collection" help text by mistake
        response = self.ask('hello can i get recommendations for some abstracy paintings or artworks')
        self.assertEqual([a['title'] for a in response.data['artworks']], ['Midnight Currents'])
        self.assertNotIn('My Collection', response.data['reply'])

    def test_answers_questions_about_an_artist(self):
        response = self.ask('tell me about Elena Marwood')
        self.assertIn('Elena Marwood', response.data['reply'])
        self.assertEqual([a['title'] for a in response.data['artworks']], ['Chapel Test'])

    def test_explains_how_to_use_the_site(self):
        response = self.ask('How do I save a painting to my favorites?')
        self.assertIn('heart', response.data['reply'])

    def test_unknown_question_gets_a_polite_answer_with_suggestions(self):
        response = self.ask('What is the weather today?')
        self.assertIn('not sure', response.data['reply'])
        self.assertTrue(response.data['suggestions'])

    def test_empty_message_is_rejected(self):
        self.assertEqual(self.ask('   ').status_code, 400)

class RecommenderTests(APITestCase):
    def setUp(self):
        self.user = make_user()
        self.liked = make_artwork('Liked', 'Landscape', 'impressionism', 'oil', ['blue', 'green'], views=10)
        self.similar = make_artwork('Similar', 'Landscape', 'impressionism', 'oil', ['blue', 'yellow'], views=10)
        self.different = make_artwork('Different', 'Abstract', 'abstract', 'acrylic', ['red'], views=10)

    def test_favorites_shape_the_recommendations(self):
        Favorite.objects.create(user=self.user, artwork=self.liked)
        artworks, personalized = recommend(self.user, limit=5)
        self.assertTrue(personalized)
        self.assertEqual([a.title for a in artworks], ['Similar', 'Different'])  # the saved one is left out

    def test_visitors_get_popular_paintings(self):
        artworks, personalized = recommend(AnonymousUser(), limit=5)
        self.assertFalse(personalized)
        self.assertEqual(len(artworks), 3)

    def test_recommendations_endpoint_works_for_visitors(self):
        response = self.client.get('/api/recommendations/')
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.data['personalized'])


@override_settings(OPENAI_API_KEY='', MEDIA_ROOT=TEMP_MEDIA)
class ImageAnalysisTests(APITestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA, ignore_errors=True)

    def setUp(self):
        cache.clear()
        make_artwork('Harbour Test', 'Landscape', 'impressionism', 'oil', ['blue', 'yellow', 'green'])

    def upload(self, **data):
        return self.client.post('/api/ai/analyze-image/', data, format='multipart')

    def test_reads_the_palette_and_finds_similar_paintings(self):
        response = self.upload(image=sample_png())
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['palette'])
        self.assertTrue(response.data['dominant_colors'])
        self.assertEqual(response.data['methods']['colors'], 'opencv-kmeans')

        # No AI key, so category and style are labelled as a demo estimate
        self.assertTrue(response.data['is_demo_result'])
        self.assertEqual(response.data['methods']['category'], 'color-matching-estimate')

        similar = response.data['similar_artworks']
        self.assertEqual(similar[0]['title'], 'Harbour Test')
        self.assertIn('match_percent', similar[0])

        analysis = AIAnalysis.objects.get()
        self.assertEqual(analysis.source, 'fallback')

    def test_files_that_are_not_images_are_rejected(self):
        text = SimpleUploadedFile('notes.txt', b'hello', content_type='text/plain')
        disguised = SimpleUploadedFile('fake.jpg', b'this is not really a picture', content_type='image/jpeg')
        for bad_file in (text, disguised):
            response = self.upload(image=bad_file)
            self.assertEqual(response.status_code, 400)
            self.assertIn('detail', response.data)
        self.assertEqual(AIAnalysis.objects.count(), 0)

    def test_missing_file_gets_a_friendly_message(self):
        response = self.upload()
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['detail'], 'Please choose an image to upload.')


@override_settings(OPENAI_API_KEY='')
class SummaryAndDownloadTests(APITestCase):
    def setUp(self):
        self.art = make_artwork('Harbour Test', 'Landscape', 'impressionism', 'oil', ['blue', 'yellow'])

    def test_summary_is_built_from_the_details_and_labelled_as_not_ai(self):
        response = self.client.get(f'/api/artworks/{self.art.id}/summary/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['source'], 'template')
        self.assertFalse(response.data['is_ai'])
        self.assertIn('Harbour Test', response.data['summary'])

    def test_pdf_download(self):
        response = self.client.get(f'/api/artworks/{self.art.id}/download/pdf/')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response['Content-Type'].startswith('application/pdf'))
        self.assertTrue(response.content.startswith(b'%PDF'))
        self.assertIn('harbour-test.pdf', response['Content-Disposition'])

    def test_word_download(self):
        response = self.client.get(f'/api/artworks/{self.art.id}/download/docx/')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.content.startswith(b'PK'))  # a .docx file is a zip archive

    def test_unknown_format_and_unknown_painting_are_404(self):
        self.assertEqual(self.client.get(f'/api/artworks/{self.art.id}/download/xyz/').status_code, 404)
        self.assertEqual(self.client.get('/api/artworks/9999/download/pdf/').status_code, 404)


class DashboardTests(APITestCase):
    def test_dashboard_needs_a_login(self):
        self.assertEqual(self.client.get('/api/dashboard/').status_code, 403)

    def test_dashboard_returns_every_section(self):
        user = make_user()
        Favorite.objects.create(user=user, artwork=make_artwork('Harbour Test'))
        self.client.force_authenticate(user)

        response = self.client.get('/api/dashboard/')
        self.assertEqual(response.status_code, 200)
        for key in ('stats', 'recently_viewed', 'favorites', 'favorite_categories',
                    'recommendations', 'collections'):
            self.assertIn(key, response.data)
        self.assertEqual(response.data['stats']['favorites'], 1)