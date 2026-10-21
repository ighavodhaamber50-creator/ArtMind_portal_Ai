from django.shortcuts import get_object_or_404
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from gallery.models import Artwork

from .summaries import get_summary


class ArtworkSummaryView(APIView):
    """GET /api/artworks/<id>/summary/

    Not rate limited: an AI summary is generated once per painting and then saved,
    so repeat requests cost nothing."""

    permission_classes = [AllowAny]

    def get(self, request, pk):
        artwork = get_object_or_404(Artwork.objects.select_related('artist', 'category'), pk=pk)
        summary, source = get_summary(artwork)
        return Response({'summary': summary, 'source': source, 'is_ai': source != 'template'})