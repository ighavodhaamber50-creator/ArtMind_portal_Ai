"""Natural-language search: turn a sentence into filters, then find matching paintings.

Two interchangeable extractors produce the same 'criteria' dictionary:
  * OpenAI  - used when OPENAI_API_KEY is set and the call succeeds
  * keywords - always available, used as the fallback
Everything after extraction is shared. With a small catalog we filter in Python;
for a large catalog these checks would move into database queries.
"""
import difflib
import json
import logging
import re

from django.conf import settings

from gallery.models import Artwork, Category

logger = logging.getLogger(__name__)

STOPWORDS = {
    'a', 'about', 'all', 'an', 'and', 'any', 'are', 'art', 'artwork', 'artworks', 'by', 'color',
    'colors', 'colour', 'colours', 'display', 'find', 'for', 'get', 'give', 'have', 'i', 'image',
    'images', 'in', 'is', 'list', 'look', 'looking', 'made', 'me', 'of', 'on', 'painted',
    'painting', 'paintings', 'picture', 'pictures', 'please', 'recommend', 'see', 'shade',
    'shades', 'show', 'some', 'style', 'that', 'the', 'theme', 'themes', 'to', 'tone', 'tones',
    'using', 'want', 'with', 'work', 'works',  'about', 'best', 'can', 'could', 'get', 'give', 'good', 'hello', 'hey', 'hi', 'just',
    'like', 'more', 'need', 'new', 'nice', 'other', 'please', 'really', 'recommendation',
    'recommendations', 'recommended', 'suggest', 'suggestion', 'suggestions', 'tell', 'would',
}
MEDIUM_WORDS = {
    'oil': 'oil', 'oils': 'oil', 'watercolor': 'watercolor', 'watercolors': 'watercolor',
    'watercolour': 'watercolor', 'watercolours': 'watercolor', 'acrylic': 'acrylic',
    'acrylics': 'acrylic', 'pastel': 'pastel', 'pastels': 'pastel', 'ink': 'ink', 'mixed': 'mixed',
}
STYLE_WORDS = {
    'impressionism': 'impressionism', 'impressionist': 'impressionism',
    'expressionism': 'expressionism', 'expressionist': 'expressionism',
    'realism': 'realism', 'realistic': 'realism', 'realist': 'realism',
    'surrealism': 'surrealism', 'surreal': 'surrealism', 'modern': 'modern',
    'classical': 'classical', 'classic': 'classical', 'contemporary': 'contemporary',
}
# 'abstract' maps to the Abstract *category*; the abstract *style* is available in the filters
CATEGORY_WORDS = {
    'abstract': 'Abstract', 'landscape': 'Landscape', 'landscapes': 'Landscape',
    'flower': 'Flower', 'flowers': 'Flower', 'floral': 'Flower', 'nature': 'Nature',
    'figurative': 'Figurative', 'figure': 'Figurative', 'figures': 'Figurative',
    'religious': 'Religious', 'spiritual': 'Religious',
}


def get_vocabulary():
    """The real values the database knows about. AI output is validated against these."""
    colors = set()
    for color_list in Artwork.objects.values_list('dominant_colors', flat=True):
        colors.update(color_list)
    return {
        'categories': list(Category.objects.values_list('name', flat=True)),
        'styles': [code for code, _ in Artwork.STYLE_CHOICES],
        'mediums': [code for code, _ in Artwork.MEDIUM_CHOICES],
        'colors': sorted(colors),
    }

def _correct_spelling(word, vocab):
    """Fix small typos in words we know ('abstracy' becomes 'abstract'). Other words are left alone."""
    if len(word) < 5 or word in STOPWORDS:
        return word
    known = [*MEDIUM_WORDS, *STYLE_WORDS, *CATEGORY_WORDS, *vocab['colors']]
    if word in known or word.rstrip('s') in known:
        return word
    close = difflib.get_close_matches(word, known, n=1, cutoff=0.82)
    return close[0] if close else word


def extract_with_keywords(query, vocab):
    """Fallback extractor: match words against known categories, styles, mediums and colors."""
    criteria = _empty_criteria()
    valid_categories = set(vocab['categories'])

    for raw_word in re.findall(r'[a-z]+', query.lower()):
        word = _correct_spelling(raw_word, vocab)
        if word in MEDIUM_WORDS:
            criteria['medium'] = MEDIUM_WORDS[word]
        elif word in STYLE_WORDS:
            criteria['style'] = STYLE_WORDS[word]
        elif CATEGORY_WORDS.get(word) in valid_categories:
            criteria['category'] = CATEGORY_WORDS[word]
        elif word in vocab['colors'] or word.rstrip('s') in vocab['colors']:
            color = word if word in vocab['colors'] else word.rstrip('s')
            if color not in criteria['colors']:
                criteria['colors'].append(color)
        elif word not in STOPWORDS and len(word) > 2:
            theme = word[:-1] if word.endswith('s') and len(word) > 3 else word
            if theme not in criteria['themes']:
                criteria['themes'].append(theme)

    criteria['themes'] = criteria['themes'][:3]
    return criteria

def _empty_criteria():
    return {'category': None, 'style': None, 'medium': None, 'colors': [], 'themes': []}




def clean_criteria(raw, vocab):
    """Keep only values we recognise, so the AI cannot invent filters."""
    criteria = _empty_criteria()
    if not isinstance(raw, dict):
        return criteria

    categories = {name.lower(): name for name in vocab['categories']}
    category = str(raw.get('category') or '').lower()
    criteria['category'] = categories.get(category)

    style = str(raw.get('style') or '').lower()
    criteria['style'] = style if style in vocab['styles'] else None

    medium = str(raw.get('medium') or '').lower()
    criteria['medium'] = medium if medium in vocab['mediums'] else None

    colors = raw.get('colors') if isinstance(raw.get('colors'), list) else []
    criteria['colors'] = [c.lower() for c in colors
                          if isinstance(c, str) and c.lower() in vocab['colors']][:3]

    themes = raw.get('themes') if isinstance(raw.get('themes'), list) else []
    criteria['themes'] = [t.lower() for t in themes
                          if isinstance(t, str) and re.fullmatch(r'[a-zA-Z]{3,20}', t)][:3]
    return criteria


def extract_with_openai(query, vocab):
    """Ask OpenAI to turn the sentence into filters. Raises an exception on any failure."""
    from openai import OpenAI  # imported here so the app still runs if the library is missing

    system_prompt = (
        'You convert art-search sentences into JSON filters. Reply with JSON only, using keys '
        '"category", "style", "medium", "colors" (list) and "themes" (list of up to 3 short '
        'lowercase subject words such as "sea" or "sunset"). Use null or an empty list when '
        'the sentence does not mention something. Allowed values - '
        f'category: {vocab["categories"]}; style: {vocab["styles"]}; '
        f'medium: {vocab["mediums"]}; colors: {vocab["colors"]}.'
    )
    client = OpenAI(api_key=settings.OPENAI_API_KEY, timeout=15.0)
    response = client.chat.completions.create(
        model=settings.OPENAI_MODEL,
        temperature=0,
        response_format={'type': 'json_object'},
        messages=[{'role': 'system', 'content': system_prompt},
                  {'role': 'user', 'content': query}],
    )
    return clean_criteria(json.loads(response.choices[0].message.content), vocab)


def parse_query(query):
    """Return (criteria, used_ai, note). Never raises: any AI problem falls back to keywords."""
    vocab = get_vocabulary()

    if settings.OPENAI_API_KEY:
        try:
            return extract_with_openai(query, vocab), True, ''
        except Exception as exc:  # bad key, network error, rate limit, invalid JSON, ...
            logger.warning('OpenAI search failed (%s); using keyword fallback', type(exc).__name__)
            note = 'The AI service is unavailable right now, so keyword matching was used.'
    else:
        note = 'No AI key is configured, so keyword matching was used.'

    return extract_with_keywords(query, vocab), False, note


def search_artworks(criteria):
    """Return (artworks, relaxed). 'relaxed' means no exact match, so these are the closest ones."""
    needed = sum(bool(criteria[key]) for key in ('category', 'style', 'medium', 'colors', 'themes'))
    if needed == 0:
        return [], False  # nothing understood in the sentence

    theme_patterns = [re.compile(rf'\b{re.escape(t)}(s|es)?\b') for t in criteria['themes']]

    scored = []
    for art in Artwork.objects.select_related('artist', 'category'):
        hits = 0
        if criteria['category'] and art.category.name == criteria['category']:
            hits += 1
        if criteria['style'] and art.style == criteria['style']:
            hits += 1
        if criteria['medium'] and art.medium == criteria['medium']:
            hits += 1
        if criteria['colors'] and any(c in art.dominant_colors for c in criteria['colors']):
            hits += 1
        if theme_patterns:
            text = ' '.join([art.title, art.description, ' '.join(art.tags)]).lower()
            if any(pattern.search(text) for pattern in theme_patterns):
                hits += 1
        scored.append((hits, art))

    exact = [art for hits, art in scored if hits == needed]
    if exact:
        return sorted(exact, key=lambda a: a.view_count, reverse=True), False

    partial = sorted((pair for pair in scored if pair[0] > 0),
                     key=lambda pair: (pair[0], pair[1].view_count), reverse=True)
    return [art for _, art in partial], True