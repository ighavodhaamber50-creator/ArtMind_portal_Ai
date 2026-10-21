"""Tests for a user's own private collection of uploaded paintings."""

import shutil
import tempfile
from io import BytesIO

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from PIL import Image
from rest_framework.test import APITestCase

from gallery.factories import TEST_PASSWORD, make_artwork, make_user

from .models import UserArtwork

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


@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class MyArtworkTests(APITestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA, ignore_errors=True)

    def setUp(self):
        self.user = make_user('amber')
        self.other = make_user('other')
        self.category_id = make_artwork('Seed Painting', 'Landscape').category_id

    def form(self, **overrides):
        data = {
            'title': 'My Sunset', 'artist_name': 'Amber', 'category': self.category_id,
            'style': 'impressionism', 'medium': 'oil', 'surface': 'canvas',
            'description': 'Painted at the beach.', 'image': sample_png(),
        }
        data.update(overrides)
        return data

    def upload(self, **overrides):
        return self.client.post('/api/my-artworks/', self.form(**overrides), format='multipart')

    def log_in(self, user):
        """Log in with a real session, like a browser. The download view is a plain Django view,
        so it reads the session and does not see the API shortcut used elsewhere in these tests."""
        self.client.force_authenticate(None)
        self.assertTrue(self.client.login(username=user.username, password=TEST_PASSWORD))

    def test_everything_needs_a_login(self):
        self.assertEqual(self.client.get('/api/my-artworks/').status_code, 403)
        self.assertEqual(self.upload().status_code, 403)

    def test_upload_saves_the_painting_and_measures_its_colors(self):
        self.client.force_authenticate(self.user)
        response = self.upload()
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['title'], 'My Sunset')
        self.assertEqual(response.data['category_name'], 'Landscape')
        self.assertTrue(response.data['dominant_colors'])
        self.assertEqual(UserArtwork.objects.filter(owner=self.user).count(), 1)

    def test_artist_name_defaults_to_the_username(self):
        self.client.force_authenticate(self.user)
        response = self.upload(artist_name='')
        self.assertEqual(response.data['artist'], 'amber')

    def test_each_user_sees_only_their_own_paintings(self):
        self.client.force_authenticate(self.user)
        self.upload()
        self.assertEqual(len(self.client.get('/api/my-artworks/').data), 1)

        self.client.force_authenticate(self.other)
        self.assertEqual(self.client.get('/api/my-artworks/').data, [])

    def test_only_the_owner_can_delete(self):
        self.client.force_authenticate(self.user)
        artwork_id = self.upload().data['id']

        self.client.force_authenticate(self.other)
        self.assertEqual(self.client.delete(f'/api/my-artworks/{artwork_id}/').status_code, 404)
        self.assertEqual(UserArtwork.objects.count(), 1)

        self.client.force_authenticate(self.user)
        self.assertEqual(self.client.delete(f'/api/my-artworks/{artwork_id}/').status_code, 204)
        self.assertEqual(UserArtwork.objects.count(), 0)

    def test_files_that_are_not_pictures_are_rejected(self):
        self.client.force_authenticate(self.user)
        notes = SimpleUploadedFile('notes.txt', b'hello', content_type='text/plain')
        response = self.upload(image=notes)
        self.assertEqual(response.status_code, 400)
        self.assertIn('detail', response.data)
        self.assertEqual(UserArtwork.objects.count(), 0)

    def test_missing_title_gets_a_friendly_message(self):
        self.client.force_authenticate(self.user)
        data = self.form()
        data.pop('title')
        response = self.client.post('/api/my-artworks/', data, format='multipart')
        self.assertEqual(response.status_code, 400)
        self.assertIn('Title', response.data['detail'])

    def test_there_is_a_limit_per_user(self):
        UserArtwork.objects.bulk_create([
            UserArtwork(owner=self.user, title=f'Painting {i}', category_id=self.category_id,
                        style='realism', medium='oil', image='user_artworks/placeholder.jpg')
            for i in range(20)
        ])
        self.client.force_authenticate(self.user)
        response = self.upload()
        self.assertEqual(response.status_code, 400)
        self.assertIn('up to 20', response.data['detail'])

    def test_owner_can_download_pdf_and_word(self):
        self.client.force_authenticate(self.user)
        artwork_id = self.upload().data['id']

        self.log_in(self.user)
        pdf = self.client.get(f'/api/my-artworks/{artwork_id}/download/pdf/')
        self.assertEqual(pdf.status_code, 200)
        self.assertTrue(pdf.content.startswith(b'%PDF'))
        self.assertIn('my-sunset.pdf', pdf['Content-Disposition'])

        word = self.client.get(f'/api/my-artworks/{artwork_id}/download/docx/')
        self.assertEqual(word.status_code, 200)
        self.assertTrue(word.content.startswith(b'PK'))

    def test_nobody_else_can_download_it(self):
        self.client.force_authenticate(self.user)
        artwork_id = self.upload().data['id']

        self.log_in(self.other)
        self.assertEqual(self.client.get(f'/api/my-artworks/{artwork_id}/download/pdf/').status_code, 404)

        self.client.logout()
        self.assertEqual(self.client.get(f'/api/my-artworks/{artwork_id}/download/pdf/').status_code, 403)