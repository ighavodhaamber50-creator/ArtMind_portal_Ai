"""ArtMind Assistant: answers art questions and helps people use the website.

OpenAI writes the answer when a key is configured. Otherwise (or if the AI call fails)
a built-in knowledge base answers, so the assistant always works.
"""

import logging
import re

from django.conf import settings

from gallery.models import Artist, Artwork, Category

from . import art_knowledge as kb
from .nl_search import (CATEGORY_WORDS, MEDIUM_WORDS, STYLE_WORDS, extract_with_keywords,
                        get_vocabulary, search_artworks)

logger = logging.getLogger(__name__)

# "recommend\w*" also catches recommends, recommended, recommendations...
SUGGESTION_INTENT = re.compile(
    r'\b(show|find|recommend\w*|suggest\w*|looking for|browse|display|see|any|want|give|get)\b')
NAV_INTENT = re.compile(
    r'\b(how do i|how can i|how to|where do i|where can i|where is|navigate|which page|menu)\b')
COMPARE_INTENT = re.compile(r'\b(difference|differ|differs|compare|comparison|versus|vs)\b')
HELP_INTENT = re.compile(r'\b(what can you do|who are you|what are you|what do you do)\b|^\s*help\W*$')
THANKS_INTENT = re.compile(r'\b(thanks|thank you|thx)\b')
GREETINGS = {'hi', 'hello', 'hey'}
COUNT_INTENT = re.compile(r'\b(how many|number of|total|count|how large|how big|size of)\b')
GALLERY_NOUNS = re.compile(r'\b(paintings?|artworks?|pieces|collection|gallery)\b')
QUALIFIERS = re.compile(r'\b(artists?|categor(?:y|ies)|favou?rites?|styles?|mediums?)\b')

# Words too general to answer a navigation question on their own
GENERIC_NAV_WORDS = {
    'save', 'saved', 'find', 'search', 'sort', 'filter', 'log', 'sign', 'account', 'recommended',
    'recommendations', 'history', 'viewed', 'identify', 'scan', 'recognize', 'recognition',
}

STYLE_QUESTION_WORDS = {**STYLE_WORDS, 'abstract': 'abstract'}
TECHNIQUE_WORDS = {'impasto': 'impasto', 'glazing': 'glazing', 'glaze': 'glazing',
                   'glazes': 'glazing', 'wash': 'wash', 'washes': 'wash'}

SUGGESTED_QUESTIONS = [
    'What is impressionism?',
    'What is the difference between watercolor and oil painting?',
    'Recommend some landscape paintings',
    'How do I save a painting to my favorites?',
]

GREETING_REPLY = ('Hello! I am the ArtMind Assistant. I can explain art styles and techniques, '
                  'recommend paintings, and help you find your way around the site.')
HELP_REPLY = ('I can explain art styles such as impressionism, painting mediums and techniques, '
              'recommend paintings from the gallery, tell you about the artists here, and help '
              'you use the website. Try one of these:')


def clean_history(raw):
    """Keep only the last few well-formed turns. Roles are limited so nobody can inject 'system'."""
    if not isinstance(raw, list):
        return []
    cleaned = []
    for item in raw[-6:]:
        if (isinstance(item, dict) and item.get('role') in ('user', 'assistant')
                and isinstance(item.get('content'), str)):
            cleaned.append({'role': item['role'], 'content': item['content'][:1000]})
    return cleaned


def find_artist(text):
    """Return the gallery artist named in the text (full name, or a last name of 4+ letters)."""
    for artist in Artist.objects.all():
        full = artist.name.lower()
        last = full.split()[-1]
        if full in text or (len(last) >= 4 and re.search(rf'\b{re.escape(last)}\b', text)):
            return artist
    return None


def find_suggestions(message):
    """Look for paintings the message asks about. Returns (artworks, searched, artist)."""
    text = message.lower()

    artist = find_artist(text)
    if artist:
        works = list(Artwork.objects.filter(artist=artist).select_related('artist', 'category')[:4])
        return works, True, artist

    if not SUGGESTION_INTENT.search(text):
        return [], False, None
    criteria = extract_with_keywords(message, get_vocabulary())
    if not any(criteria[key] for key in ('category', 'style', 'medium', 'colors')):
        return [], False, None
    artworks, _relaxed = search_artworks(criteria)
    return artworks[:4], True, None


def _ordered_unique(items):
    result = []
    for item in items:
        if item not in result:
            result.append(item)
    return result


def fallback_reply(message, artworks, searched, artist):
    """Built-in answers. Returns (reply, suggested_questions, paintings_to_show)."""
    text = message.lower()
    words = re.findall(r'[a-z]+', text)
    word_set = set(words)

    if word_set & GREETINGS and len(words) <= 4:
        return GREETING_REPLY, SUGGESTED_QUESTIONS, []

    if artist:
        intro = artist.name + (f' ({artist.nationality})' if artist.nationality else '')
        reply = f'{intro}. {artist.bio}'.strip()
        if artworks:
            reply += ' In this gallery: ' + '; '.join(a.title for a in artworks) + '.'
        return reply, [], artworks

    if artworks:
        titles = '; '.join(f'{a.title} by {a.artist.name}' for a in artworks)
        if len(artworks) == 1:
            lead, verb = 'Here is one painting', 'matches'
        else:
            lead, verb = f'Here are {len(artworks)} paintings', 'match'
        return f'{lead} from the gallery that {verb}: {titles}.', [], artworks
    if searched:
        return ('I could not find a painting matching that. Try another color, style or medium, '
                'for example "blue watercolor landscape".'), SUGGESTED_QUESTIONS, []

    if HELP_INTENT.search(text):
        return HELP_REPLY, SUGGESTED_QUESTIONS, []
    if THANKS_INTENT.search(text) and len(words) <= 6:
        return 'You are welcome! Ask me anything else about art or the gallery.', [], []

    if NAV_INTENT.search(text):
        for keywords, answer in kb.NAVIGATION:
            if word_set & keywords:
                return answer, [], []

    mediums = _ordered_unique(MEDIUM_WORDS[w] for w in words if w in MEDIUM_WORDS)
    if COMPARE_INTENT.search(text) and len(mediums) >= 2:
        labels = dict(Artwork.MEDIUM_CHOICES)
        first, second = mediums[:2]
        return (f'Here is how {labels[first]} and {labels[second]} differ. '
                f'{labels[first]}: {kb.MEDIUM_FACTS[first]} '
                f'{labels[second]}: {kb.MEDIUM_FACTS[second]}'), [], []

    for word in words:
        if word in TECHNIQUE_WORDS:
            return kb.TECHNIQUE_FACTS[TECHNIQUE_WORDS[word]], [], []
    for word in words:
        if word in STYLE_QUESTION_WORDS:
            return kb.STYLE_FACTS[STYLE_QUESTION_WORDS[word]], [], []
    if mediums:
        return kb.MEDIUM_FACTS[mediums[0]], [], []

    for word in words:
        name = CATEGORY_WORDS.get(word)
        category = Category.objects.filter(name=name).first() if name else None
        if category:
            return (f'{category.name}: {category.description} '
                    f'Ask me to "show {category.name.lower()} paintings" to see some.'), [], []

    # A website topic named without a "how do I" phrase, such as "can I see my favorites"
    for keywords, answer in kb.NAVIGATION:
        if word_set & (keywords - GENERIC_NAV_WORDS):
            return answer, [], []

    return ('I am not sure about that one yet. I can help with art styles such as '
            'impressionism, painting mediums and techniques, finding paintings, the artists in '
            'this gallery, and using the website. Try one of these:'), SUGGESTED_QUESTIONS, []

def ask_openai(message, history, artworks, artist):
    """Let OpenAI write the answer. Raises an exception on any failure."""
    from openai import OpenAI  # imported here so the app still runs if the library is missing

    vocab = get_vocabulary()
    system_prompt = (
        'You are ArtMind Assistant, a friendly guide inside ArtMind AI Portal, a digital '
        'painting gallery. Answer questions about paintings, artists, artistic styles, '
        'painting techniques, art categories, artwork recommendations and how to use the '
        'website. Keep answers under 120 words, in plain text. If asked about something '
        'unrelated to art or the website, politely say you can only help with those. '
        'Never claim a painting exists in the gallery unless it is listed below. '
        f'Gallery categories: {", ".join(vocab["categories"])}. '
        'Website pages: Home, Gallery, Analyze Artwork, My Collection, Login, Register. '
        'Logged-in users can save favorites and get personalized recommendations.'
    )
    if artist:
        system_prompt += (f' The user is asking about the gallery artist {artist.name} '
                          f'({artist.nationality}): {artist.bio}')
    if artworks:
        listing = '; '.join(
            f'{a.title} by {a.artist.name} ({a.category.name}, {a.get_style_display()}, '
            f'{a.get_medium_display()})' for a in artworks)
        system_prompt += f' Paintings in the gallery that match this request: {listing}.'

    client = OpenAI(api_key=settings.OPENAI_API_KEY, timeout=20.0)
    response = client.chat.completions.create(
        model=settings.OPENAI_MODEL,
        temperature=0.5,
        max_completion_tokens=300,
        messages=[{'role': 'system', 'content': system_prompt}, *history,
                  {'role': 'user', 'content': message}],
    )
    reply = (response.choices[0].message.content or '').strip()
    if not reply:
        raise ValueError('empty reply from the AI service')
    return reply

def painting_count_reply(message):
    """Answer 'how many paintings...' from the database. Returns None for anything else."""
    text = message.lower()
    if not (COUNT_INTENT.search(text) and GALLERY_NOUNS.search(text)) or QUALIFIERS.search(text):
        return None
    criteria = extract_with_keywords(message, get_vocabulary())
    if any(criteria[key] for key in ('category', 'style', 'medium', 'colors')):
        return None  # a filtered count, such as landscape paintings, is not handled here
    total = Artwork.objects.count()
    if total == 0:
        return 'The gallery has no paintings yet.'
    return f'The gallery has {total} painting{"" if total == 1 else "s"}.'


def chat(message, history):
    """Return {'reply', 'used_ai', 'note', 'artworks', 'suggestions'}. Never raises for AI problems."""
    count_reply = painting_count_reply(message)
    if count_reply:
        return {'reply': count_reply, 'used_ai': False, 'note': '', 'artworks': [], 'suggestions': []}

    artworks, searched, artist = find_suggestions(message)

    if settings.OPENAI_API_KEY:
        try:
            reply = ask_openai(message, history, artworks, artist)
            return {'reply': reply, 'used_ai': True, 'note': '',
                    'artworks': artworks, 'suggestions': []}
        except Exception as exc:  # bad key, network error, rate limit, empty reply, ...
            logger.warning('OpenAI chat failed (%s: %s); using built-in answers',
                           type(exc).__name__, str(exc)[:200])
            note = 'The AI service is unavailable right now, so the built-in answers were used.'
    else:
        note = 'No AI key is configured, so the built-in answers were used.'

    reply, suggestions, shown = fallback_reply(message, artworks, searched, artist)
    return {'reply': reply, 'used_ai': False, 'note': note,
            'artworks': shown, 'suggestions': suggestions}