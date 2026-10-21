from django.core.cache import cache
from django.test import override_settings
from rest_framework.test import APITestCase

from gallery.factories import make_artwork


@override_settings(OPENAI_API_KEY='')
class PaintingCountTests(APITestCase):
    def setUp(self):
        cache.clear()
        for i in range(3):
            make_artwork(f'Painting {i}')

    def ask(self, message):
        return self.client.post('/api/ai/chat/', {'message': message}, format='json')

    def test_painting_count_comes_from_the_database(self):
        for question in ('How many paintings are available?', 'How many artworks do we have?',
                         'Can you count the artworks?', 'How large is the collection?'):
            with self.subTest(question=question):
                response = self.ask(question)
                self.assertIn('3 paintings', response.data['reply'])
        make_artwork('Painting 3')
        self.assertIn('4 paintings', self.ask('How many paintings are available?').data['reply'])