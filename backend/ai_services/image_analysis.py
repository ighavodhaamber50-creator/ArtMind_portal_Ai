"""Artwork image analysis.

Real parts:   dominant colors (OpenCV k-means) and color-based similarity to gallery paintings.
Category/style: identified by an OpenAI vision model when a key is set; otherwise only
*estimated* from the most color-similar gallery paintings and labeled as a demo result.
"""

import base64
import io
import json
import logging
from collections import Counter

import cv2
import numpy as np
from django.conf import settings
from PIL import Image, ImageOps, UnidentifiedImageError

from gallery.models import Artwork

from .nl_search import clean_criteria, get_vocabulary

logger = logging.getLogger(__name__)

ALLOWED_FORMATS = {'JPEG', 'PNG', 'WEBP'}
MAX_PIXELS = 25_000_000   # refuse enormous images before decoding them
MIN_SIDE = 32
SAMPLE_SIZE = 120         # colors are measured on a small copy, which is faster and just as accurate
NUM_CLUSTERS = 6

# Color names, matching the ones used on the gallery paintings (plus black and gray for photos)
NAMED_COLORS = {
    'blue': (40, 90, 170), 'green': (50, 130, 80), 'yellow': (235, 200, 70),
    'red': (190, 50, 50), 'orange': (230, 130, 50), 'purple': (120, 70, 150),
    'pink': (230, 140, 170), 'white': (240, 240, 235), 'brown': (110, 75, 50),
    'teal': (40, 140, 140), 'gold': (212, 175, 55), 'black': (25, 25, 25),
    'gray': (128, 128, 128),
}
PALETTE_NAMES = list(NAMED_COLORS)


class ImageRejected(Exception):
    """The upload cannot be used. The message is safe to show to the user."""


def _to_lab(rgb_rows):
    """Convert RGB colors to Lab, where distances match how people see color differences."""
    array = np.array(rgb_rows, dtype=np.uint8).reshape(-1, 1, 3)
    return cv2.cvtColor(array, cv2.COLOR_RGB2LAB).reshape(-1, 3).astype(np.float32)


_PALETTE_LAB = _to_lab(list(NAMED_COLORS.values()))


def load_image(upload):
    """Validate the upload and return a clean RGB Pillow image (max 1024 px on its longest side)."""
    try:
        upload.seek(0)
        image = Image.open(upload)  # lazy: reads the header only
        if image.format not in ALLOWED_FORMATS:
            raise ImageRejected('Please upload a JPG, PNG or WEBP image.')
        if image.width * image.height > MAX_PIXELS:
            raise ImageRejected('That image has too many pixels. Please upload a smaller one.')
        if min(image.size) < MIN_SIDE:
            raise ImageRejected('That image is too small to analyze.')

        image = ImageOps.exif_transpose(image)  # fix photos that were taken sideways
        if image.mode in ('RGBA', 'LA') or (image.mode == 'P' and 'transparency' in image.info):
            rgba = image.convert('RGBA')
            background = Image.new('RGB', rgba.size, (255, 255, 255))
            background.paste(rgba, mask=rgba.split()[3])  # transparent areas become white
            image = background
        else:
            image = image.convert('RGB')
    except ImageRejected:
        raise
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError):
        raise ImageRejected('We could not read that file as an image.')

    image.thumbnail((1024, 1024))
    return image


def analyze_colors(image):
    """Real analysis. Returns (top 3 color names, palette for display, {color name: share})."""
    sample = image.copy()
    sample.thumbnail((SAMPLE_SIZE, SAMPLE_SIZE))
    pixels = np.array(sample, dtype=np.float32).reshape(-1, 3)

    cv2.setRNGSeed(42)  # the same image always gives the same result
    k = min(NUM_CLUSTERS, len(pixels))
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 20, 1.0)
    _, labels, centers = cv2.kmeans(pixels, k, None, criteria, 3, cv2.KMEANS_PP_CENTERS)

    counts = np.bincount(labels.flatten(), minlength=k)
    total = float(counts.sum())
    centers = np.clip(centers, 0, 255).round().astype(np.uint8)

    # Name each cluster by its nearest named color
    distances = np.linalg.norm(_to_lab(centers)[:, None, :] - _PALETTE_LAB[None, :, :], axis=2)
    nearest = distances.argmin(axis=1)

    palette, weights = [], Counter()
    for index in np.argsort(-counts):
        name = PALETTE_NAMES[int(nearest[index])]
        share = float(counts[index]) / total
        r, g, b = (int(v) for v in centers[index])
        palette.append({'name': name, 'hex': f'#{r:02x}{g:02x}{b:02x}', 'percent': int(round(100 * share))})
        weights[name] += share

    dominant = [name for name, _ in weights.most_common(3)]
    return dominant, palette, dict(weights)


def find_similar(weights, limit=5):
    """Real computation: how much of the image's color falls inside each painting's palette.

    Returns [(share between 0 and 1, artwork)], best match first."""
    scored = []
    for artwork in Artwork.objects.select_related('artist', 'category'):
        share = sum(weights.get(color, 0) for color in set(artwork.dominant_colors))
        scored.append((min(share, 1.0), artwork))
    scored.sort(key=lambda pair: (pair[0], pair[1].view_count), reverse=True)
    return scored[:limit]


def estimate_from_similar(scored):
    """Demo estimate (NOT AI): the most common category and style among the closest color matches."""
    top = [artwork for _, artwork in scored[:5]]
    if not top:
        return None, None
    category = Counter(a.category.name for a in top).most_common(1)[0][0]
    style = Counter(a.style for a in top).most_common(1)[0][0]
    return category, style


def classify_with_openai(image, vocab):
    """Ask an OpenAI vision model for category and style. Raises an exception on any failure."""
    from openai import OpenAI  # imported here so the app still runs if the library is missing

    buffer = io.BytesIO()
    image.save(buffer, 'JPEG', quality=85)
    data_url = 'data:image/jpeg;base64,' + base64.b64encode(buffer.getvalue()).decode()

    prompt = ('You are an art expert. Look at this painting and reply with JSON only: '
              '{"category": ..., "style": ...}. '
              f'Choose category from {vocab["categories"]} and style from {vocab["styles"]}. '
              'Use null for either one if nothing fits.')
    client = OpenAI(api_key=settings.OPENAI_API_KEY, timeout=30.0)
    response = client.chat.completions.create(
        model=settings.OPENAI_MODEL,
        temperature=0,
        response_format={'type': 'json_object'},
        messages=[{'role': 'user', 'content': [
            {'type': 'text', 'text': prompt},
            {'type': 'image_url', 'image_url': {'url': data_url, 'detail': 'low'}},
        ]}],
    )
    criteria = clean_criteria(json.loads(response.choices[0].message.content), vocab)
    if not (criteria['category'] or criteria['style']):
        raise ValueError('the model returned no usable category or style')
    return criteria['category'], criteria['style']


def analyze_artwork(image):
    """Run the whole analysis and report honestly how each part was produced."""
    dominant, palette, weights = analyze_colors(image)
    similar = find_similar(weights)

    category = style = None
    methods = {'colors': 'opencv-kmeans'}
    ai_problem = False

    if settings.OPENAI_API_KEY:
        try:
            category, style = classify_with_openai(image, get_vocabulary())
            methods['category'] = methods['style'] = 'openai-vision'
        except Exception as exc:  # bad key, network error, model without vision, ...
            ai_problem = True
            logger.warning('OpenAI image analysis failed (%s: %s); using color-based estimate',
                           type(exc).__name__, str(exc)[:200])

    is_demo = 'category' not in methods
    if is_demo:
        category, style = estimate_from_similar(similar)
        methods['category'] = methods['style'] = 'color-matching-estimate'
        notice = ('Colors were measured from your image with OpenCV (a real analysis). Category '
                  'and style are only estimates based on color similarity to gallery paintings. '
                  'This is a demo result, not AI recognition.')
        if ai_problem:
            notice += ' The AI service was unavailable, so it could not be used.'
        else:
            notice += ' Add an OpenAI key to enable AI-based recognition.'
    else:
        notice = ('Category and style were identified by an AI vision model. Colors and similar '
                  'paintings were measured from your image with OpenCV.')

    return {
        'category': category, 'style': style, 'dominant_colors': dominant, 'palette': palette,
        'similar': similar, 'methods': methods, 'is_demo': is_demo, 'notice': notice,
    }