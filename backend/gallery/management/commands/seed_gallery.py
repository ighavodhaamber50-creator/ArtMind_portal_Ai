"""Load sample categories, artists, and artworks. Safe to run more than once.

The paintings are generated placeholders (drawn with Pillow), not real artworks.
Replace any image in Django Admin with a real one at any time.
"""

import math
import random
from io import BytesIO

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from PIL import Image, ImageDraw

from gallery.models import Artist, Artwork, Category

W, H = 800, 600

COLORS = {
    'blue': (40, 90, 170), 'green': (50, 130, 80), 'yellow': (235, 200, 70),
    'red': (190, 50, 50), 'orange': (230, 130, 50), 'purple': (120, 70, 150),
    'pink': (230, 140, 170), 'white': (240, 240, 235), 'brown': (110, 75, 50),
    'teal': (40, 140, 140), 'gold': (212, 175, 55),
}

CATEGORIES = [
    ('Abstract', 'Art built from shape, color, and form rather than recognizable scenes.'),
    ('Landscape', 'Views of land, sea, and sky.'),
    ('Flower', 'Floral studies and still lifes.'),
    ('Nature', 'Forests, rivers, wildlife, and untouched places.'),
    ('Figurative', 'Paintings of people and the human form.'),
    ('Religious', 'Sacred and spiritual subjects.'),
]

ARTISTS = {
    'Elena Marwood': ('British', 'Painter of light and water, working mostly in oils.'),
    'Tomas Ilves': ('Estonian', 'Realist painter of forests and quiet valleys.'),
    'Mira Okonkwo': ('Nigerian', 'Abstract painter exploring color and rhythm.'),
    'Daniel Hartwell': ('American', 'Expressionist known for bold, emotional color.'),
    'Sofia Lindqvist': ('Swedish', 'Floral and garden studies in oil and pastel.'),
    'Kwame Adeyemi': ('Ghanaian', 'Contemporary painter of landscapes and everyday life.'),
    'Lucia Fontaine': ('French', 'Portraits and still lifes in a realist tradition.'),
    'Raphael Doss': ('Italian', 'Classical painter of sacred scenes.'),
}

# (title, artist, category, style, medium, surface, colors, tags, description)
ARTWORKS = [
    ('Blue Resonance', 'Mira Okonkwo', 'Abstract', 'abstract', 'acrylic', 'canvas',
     ['blue', 'white', 'teal'], ['geometric', 'calm', 'modern'],
     'Overlapping blue forms that echo like ripples across a still surface.'),
    ('Fractured Sunrise', 'Daniel Hartwell', 'Abstract', 'expressionism', 'oil', 'canvas',
     ['orange', 'red', 'yellow'], ['warm', 'energy', 'sunrise'],
     'Sharp bursts of warm color break the canvas like morning light.'),
    ('Midnight Currents', 'Mira Okonkwo', 'Abstract', 'modern', 'mixed', 'board',
     ['blue', 'purple', 'gold'], ['night', 'flow', 'modern'],
     'Deep blues and violets with flecks of gold, suggesting moving water at night.'),

    ('Harbour at First Light', 'Elena Marwood', 'Landscape', 'impressionism', 'oil', 'canvas',
     ['blue', 'yellow', 'green'], ['sea', 'sunrise', 'harbour'],
     'Soft brushwork captures early light settling over a quiet harbour.'),
    ('Valley After Rain', 'Tomas Ilves', 'Landscape', 'realism', 'watercolor', 'paper',
     ['green', 'blue', 'brown'], ['valley', 'rain', 'hills'],
     'Layered hills under a clearing sky, painted in transparent washes.'),
    ('Savannah Dusk', 'Kwame Adeyemi', 'Landscape', 'contemporary', 'acrylic', 'canvas',
     ['orange', 'red', 'brown'], ['sunset', 'savannah', 'warm'],
     'A wide horizon glowing red and orange as the day ends.'),

    ('Late Summer Sunflowers', 'Sofia Lindqvist', 'Flower', 'impressionism', 'oil', 'canvas',
     ['yellow', 'green', 'brown'], ['sunflower', 'summer', 'garden'],
     'Heavy sunflower heads leaning toward the last warm days of the season.'),
    ('Pink Peonies in Bloom', 'Lucia Fontaine', 'Flower', 'realism', 'watercolor', 'paper',
     ['pink', 'green', 'white'], ['peony', 'spring', 'delicate'],
     'Delicate peonies rendered with fine, translucent layers of watercolor.'),
    ('Lavender Field Study', 'Sofia Lindqvist', 'Flower', 'impressionism', 'pastel', 'paper',
     ['purple', 'green', 'blue'], ['lavender', 'field', 'summer'],
     'Rows of lavender fading into a hazy blue distance.'),

    ('Forest Mirror', 'Tomas Ilves', 'Nature', 'realism', 'oil', 'canvas',
     ['green', 'teal', 'brown'], ['forest', 'lake', 'reflection'],
     'Tall trees reflected in a still woodland pond.'),
    ('Misty Pine Ridge', 'Elena Marwood', 'Nature', 'contemporary', 'watercolor', 'paper',
     ['green', 'blue', 'white'], ['pine', 'mist', 'mountain'],
     'Pine silhouettes dissolving into morning mist.'),
    ('River Under Autumn Leaves', 'Kwame Adeyemi', 'Nature', 'impressionism', 'oil', 'wood',
     ['orange', 'red', 'gold'], ['autumn', 'river', 'leaves'],
     'A slow river carrying fallen leaves beneath a canopy of gold and red.'),

    ('The Reader', 'Lucia Fontaine', 'Figurative', 'realism', 'oil', 'canvas',
     ['brown', 'red', 'gold'], ['portrait', 'indoor', 'quiet'],
     'A figure absorbed in a book, lit by warm window light.'),
    ('Two Women at the Market', 'Kwame Adeyemi', 'Figurative', 'expressionism', 'acrylic', 'canvas',
     ['orange', 'blue', 'yellow'], ['market', 'everyday', 'colorful'],
     'Two figures framed by bright market stalls, painted in lively color.'),
    ('Portrait in Blue', 'Daniel Hartwell', 'Figurative', 'modern', 'oil', 'canvas',
     ['blue', 'white', 'brown'], ['portrait', 'blue', 'modern'],
     'A calm portrait built almost entirely from shades of blue.'),

    ('Light Through the Arch', 'Raphael Doss', 'Religious', 'classical', 'oil', 'wood',
     ['gold', 'blue', 'white'], ['arch', 'light', 'sacred'],
     'Rays of golden light pouring through a stone arch.'),
    ("The Shepherd's Prayer", 'Raphael Doss', 'Religious', 'classical', 'oil', 'canvas',
     ['gold', 'brown', 'red'], ['prayer', 'shepherd', 'devotion'],
     'A shepherd kneeling at dusk, painted in the warm tones of the old masters.'),
    ('Dawn Over the Chapel', 'Elena Marwood', 'Religious', 'impressionism', 'oil', 'canvas',
     ['orange', 'purple', 'gold'], ['chapel', 'dawn', 'peaceful'],
     'A small chapel on a hill as the first light touches its walls.'),
]


# ---------- tiny color helpers ----------
def mix(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def lighten(c):
    return mix(c, (255, 255, 255), 0.4)


def darken(c):
    return mix(c, (0, 0, 0), 0.4)


def gradient(draw, top, bottom):
    for y in range(H):
        draw.line([(0, y), (W, y)], fill=mix(top, bottom, y / H))


# ---------- one painter per category ----------
def paint_abstract(draw, pal, rnd):
    gradient(draw, pal[0], darken(pal[-1]))
    for _ in range(14):
        c, x, y, r = rnd.choice(pal), rnd.randint(0, W), rnd.randint(0, H), rnd.randint(40, 170)
        box = [x - r, y - r, x + r, y + r]
        draw.ellipse(box, fill=c) if rnd.random() < 0.5 else draw.rectangle(box, fill=c)


def paint_landscape(draw, pal, rnd):
    gradient(draw, pal[0], lighten(pal[1]))
    draw.ellipse([560, 90, 680, 210], fill=COLORS['gold'])  # sun
    for layer in range(3):  # three rows of hills, darker toward the front
        base = 330 + layer * 80
        points = [(0, H)] + [(x, base + rnd.randint(-60, 40)) for x in range(0, W + 1, 100)] + [(W, H)]
        draw.polygon(points, fill=mix(pal[(layer + 1) % len(pal)], (20, 40, 30), 0.15 * layer))


def paint_flower(draw, pal, rnd):
    gradient(draw, lighten(pal[-1]), mix(pal[-1], (30, 60, 30), 0.5))
    for _ in range(6):
        cx, cy, r = rnd.randint(80, W - 80), rnd.randint(150, 350), rnd.randint(40, 70)
        draw.line([(cx, H), (cx, cy)], fill=(40, 110, 60), width=8)
        petal = rnd.choice(pal[:2])
        for k in range(8):  # eight petals around the center
            a = k * math.pi / 4
            px, py = cx + math.cos(a) * r, cy + math.sin(a) * r
            draw.ellipse([px - r * 0.6, py - r * 0.6, px + r * 0.6, py + r * 0.6], fill=petal)
        draw.ellipse([cx - r * 0.5, cy - r * 0.5, cx + r * 0.5, cy + r * 0.5], fill=COLORS['gold'])


def paint_nature(draw, pal, rnd):
    gradient(draw, lighten(pal[1]), lighten(pal[0]))
    draw.rectangle([0, 380, W, H], fill=darken(pal[0]))
    draw.ellipse([150, 430, 650, 560], fill=lighten(pal[-1]))  # pond
    for _ in range(9):
        x, base, h = rnd.randint(0, W), rnd.randint(330, 420), rnd.randint(140, 260)
        draw.rectangle([x - 6, base - 20, x + 6, base], fill=COLORS['brown'])
        for layer in range(3):  # three stacked triangles make a pine
            top, half = base - h + layer * h * 0.25, 30 + layer * 22
            draw.polygon([(x, top), (x - half, top + h * 0.4), (x + half, top + h * 0.4)],
                         fill=mix(pal[0], (10, 50, 20), 0.2 * layer))


def paint_figurative(draw, pal, rnd):
    gradient(draw, lighten(pal[0]), pal[-1])
    for cx in (rnd.randint(220, 300), rnd.randint(480, 580)):
        c = rnd.choice(pal)
        draw.ellipse([cx - 45, 140, cx + 45, 230], fill=mix(c, (255, 224, 189), 0.6))  # head
        draw.polygon([(cx - 110, H), (cx - 60, 250), (cx + 60, 250), (cx + 110, H)], fill=darken(c))


def paint_religious(draw, pal, rnd):
    gradient(draw, darken(pal[1]), pal[0])
    cx = W // 2
    for k in range(-8, 9):  # rays of light
        draw.line([(cx, 120), (cx + k * 70, H)], fill=lighten(pal[0]), width=3)
    draw.rectangle([cx - 140, 220, cx + 140, H], fill=darken(pal[-1]))
    draw.pieslice([cx - 140, 80, cx + 140, 360], 180, 360, fill=darken(pal[-1]))  # arch top
    draw.ellipse([cx - 60, 150, cx + 60, 270], outline=COLORS['gold'], width=8)  # halo


PAINTERS = {
    'Abstract': paint_abstract, 'Landscape': paint_landscape, 'Flower': paint_flower,
    'Nature': paint_nature, 'Figurative': paint_figurative, 'Religious': paint_religious,
}


class Command(BaseCommand):
    help = 'Load sample categories, artists, and artworks with generated placeholder images.'

    def handle(self, *args, **options):
        categories = {}
        for name, description in CATEGORIES:
            categories[name], _ = Category.objects.get_or_create(
                name=name, defaults={'slug': slugify(name), 'description': description})

        artists = {}
        for name, (nationality, bio) in ARTISTS.items():
            artists[name], _ = Artist.objects.get_or_create(
                name=name, defaults={'nationality': nationality, 'bio': bio})

        created = 0
        for title, artist, category, style, medium, surface, colors, tags, description in ARTWORKS:
            if Artwork.objects.filter(title=title).exists():
                continue  # already loaded on an earlier run

            rnd = random.Random(title)  # same title always gives the same picture
            img = Image.new('RGB', (W, H))
            PAINTERS[category](ImageDraw.Draw(img), [COLORS[c] for c in colors], rnd)
            buffer = BytesIO()
            img.save(buffer, 'JPEG', quality=88)

            artwork = Artwork(
                title=title, artist=artists[artist], category=categories[category],
                style=style, medium=medium, surface=surface, description=description,
                dominant_colors=colors, tags=tags,
                view_count=rnd.randint(5, 120),  # demo numbers so analytics has something to show
            )
            artwork.image.save(f'{slugify(title)}.jpg', ContentFile(buffer.getvalue()), save=False)
            artwork.save()
            created += 1

        self.stdout.write(self.style.SUCCESS(
            f'Done: {len(categories)} categories, {len(artists)} artists, {created} new artworks.'))