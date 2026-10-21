import os

from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404
from django.utils.text import slugify
from django.views.decorators.http import require_GET

from gallery.models import Artwork

from .exports import build_docx, build_pdf
from .summaries import get_summary

FORMATS = {
    'pdf': ('application/pdf', build_pdf),
    'docx': ('application/vnd.openxmlformats-officedocument.wordprocessingml.document', build_docx),
}


@require_GET
def download_artwork(request, pk, kind):
    """GET /api/artworks/<id>/download/pdf/  or  .../download/docx/

    (A plain Django view, because DRF reserves '?format=' for its own use.)"""
    if kind not in FORMATS:
        raise Http404('Unknown download format.')

    artwork = get_object_or_404(Artwork.objects.select_related('artist', 'category'), pk=pk)
    summary, source = get_summary(artwork)
    image_path = artwork.image.path if artwork.image and os.path.exists(artwork.image.path) else None

    content_type, build = FORMATS[kind]
    response = HttpResponse(build(artwork, summary, source != 'template', image_path),
                            content_type=content_type)
    response['Content-Disposition'] = f'attachment; filename="{slugify(artwork.title) or "painting"}.{kind}"'
    return response