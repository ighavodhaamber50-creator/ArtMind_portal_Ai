"""Short written summaries of paintings.

AI-written when an OpenAI key is configured (then saved on the painting, so each one is
generated only once). Otherwise the summary is assembled from the painting's own details, and
the API says so, so the site never passes it off as AI.
"""

import logging

from django.conf import settings

from gallery.models import Artwork

logger = logging.getLogger(__name__)


def _join(items):
    items = [str(item) for item in items if item]
    if len(items) <= 1:
        return ''.join(items)
    return ', '.join(items[:-1]) + ' and ' + items[-1]


def template_summary(artwork):
    """Not AI: a sentence or two built from the painting's data."""
    category = artwork.category.name.lower()
    article = 'an' if category[0] in 'aeiou' else 'a'
    text = (f'{artwork.title} is {article} {category} painting by {artwork.artist.name}, '
            f'painted in {artwork.get_medium_display().lower()} on '
            f'{artwork.get_surface_display().lower()}. Its style is {artwork.get_style_display()}.')
    if artwork.dominant_colors:
        text += f' Its palette is built around {_join(artwork.dominant_colors[:3])}.'
    if artwork.tags:
        text += f' It touches on {_join(artwork.tags[:3])}.'
    return text


def ai_summary(artwork):
    """Ask OpenAI for a short summary. Raises an exception on any failure."""
    from openai import OpenAI  # imported here so the app still runs if the library is missing

    facts = (
        f'Title: {artwork.title}\nArtist: {artwork.artist.name}\n'
        f'Category: {artwork.category.name}\nStyle: {artwork.get_style_display()}\n'
        f'Medium: {artwork.get_medium_display()} on {artwork.get_surface_display()}\n'
        f'Dominant colors: {", ".join(artwork.dominant_colors)}\n'
        f'Tags: {", ".join(artwork.tags)}\nDescription: {artwork.description}'
    )
    client = OpenAI(api_key=settings.OPENAI_API_KEY, timeout=20.0)
    response = client.chat.completions.create(
        model=settings.OPENAI_MODEL,
        temperature=0.6,
        max_completion_tokens=200,
        messages=[
            {'role': 'system', 'content': (
                'You write short museum-style summaries of paintings for a gallery website. '
                'Write 2 or 3 sentences, under 70 words, in plain text. Use only the facts '
                'provided. Do not invent history, exhibitions, prices or biography.')},
            {'role': 'user', 'content': facts},
        ],
    )
    text = (response.choices[0].message.content or '').strip()
    if not text:
        raise ValueError('empty summary from the AI service')
    return text


def get_summary(artwork):
    """Return (text, source). Source is 'saved', 'openai' or 'template'."""
    if artwork.ai_summary:
        return artwork.ai_summary, 'saved'

    if settings.OPENAI_API_KEY:
        try:
            text = ai_summary(artwork)
            Artwork.objects.filter(pk=artwork.pk).update(ai_summary=text)  # generate once, reuse after
            return text, 'openai'
        except Exception as exc:  # bad key, network error, rate limit, ...
            logger.warning('OpenAI summary failed (%s: %s); using the built summary',
                           type(exc).__name__, str(exc)[:200])

    return template_summary(artwork), 'template'