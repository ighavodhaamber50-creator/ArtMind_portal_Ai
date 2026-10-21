"""A user's own private collection: add paintings, list them, delete them, download details."""

import io
import os
import uuid

from django.core.files.base import ContentFile
from django.db import OperationalError
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from django.utils.text import slugify
from django.views.decorators.http import require_GET
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from ai_services.export_views import FORMATS
from ai_services.image_analysis import ImageRejected, analyze_colors, load_image
from ai_services.summaries import template_summary

from .models import UserArtwork
from .serializers import UserArtworkInputSerializer, UserArtworkSerializer

MAX_PER_USER = 20


def first_error(errors):
    """Turn serializer errors into one friendly sentence."""
    field, messages = next(iter(errors.items()))
    message = str(messages[0])
    if field in ('image', 'non_field_errors'):
        return message
    return f'{field.replace("_", " ").capitalize()}: {message}'


class MyArtworksView(GenericAPIView):
    """GET lists your artworks. POST (a form with a picture) adds one."""

    serializer_class = UserArtworkInputSerializer  # also gives the browsable API a form
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get(self, request):
        artworks = UserArtwork.objects.filter(owner=request.user).select_related('category', 'owner')
        return Response(UserArtworkSerializer(artworks, many=True, context={'request': request}).data)

    def post(self, request):
        if UserArtwork.objects.filter(owner=request.user).count() >= MAX_PER_USER:
            return Response(
                {'detail': f'You can keep up to {MAX_PER_USER} artworks. Delete one to add another.'},
                status=status.HTTP_400_BAD_REQUEST)

        serializer = UserArtworkInputSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({'detail': first_error(serializer.errors)}, status=status.HTTP_400_BAD_REQUEST)
        data = serializer.validated_data

        try:
            image = load_image(data['image'])  # checks it is a real picture and strips metadata
        except ImageRejected as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        colors, _palette, _weights = analyze_colors(image)  # real analysis of the uploaded picture

        buffer = io.BytesIO()
        image.save(buffer, 'JPEG', quality=90)
        artwork = UserArtwork(
            owner=request.user,
            title=data['title'].strip(),
            artist_name=data.get('artist_name', '').strip(),
            category=data['category'],
            style=data['style'],
            medium=data['medium'],
            surface=data.get('surface', 'canvas'),
            description=data.get('description', '').strip(),
            dominant_colors=colors,
        )
        artwork.image.save(f'{uuid.uuid4().hex}.jpg', ContentFile(buffer.getvalue()), save=False)

        try:
            artwork.save()
        except OperationalError:
            artwork.image.delete(save=False)  # do not leave an orphan file behind
            return Response({'detail': 'The server is busy right now. Please try again in a moment.'},
                            status=status.HTTP_503_SERVICE_UNAVAILABLE)

        return Response(UserArtworkSerializer(artwork, context={'request': request}).data,
                        status=status.HTTP_201_CREATED)


class MyArtworkDetailView(APIView):
    """DELETE removes one of your artworks (and its picture)."""

    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        artwork = get_object_or_404(UserArtwork, pk=pk, owner=request.user)  # others get a 404
        artwork.image.delete(save=False)
        artwork.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@require_GET
def download_my_artwork(request, pk, kind):
    """GET /api/my-artworks/<id>/download/pdf/  or  .../docx/  (owner only)"""
    if not request.user.is_authenticated:
        return JsonResponse({'detail': 'Please log in to continue.'}, status=403)
    if kind not in FORMATS:
        raise Http404('Unknown download format.')

    artwork = get_object_or_404(
        UserArtwork.objects.select_related('category', 'owner'), pk=pk, owner=request.user)
    image_path = artwork.image.path if artwork.image and os.path.exists(artwork.image.path) else None

    content_type, build = FORMATS[kind]
    response = HttpResponse(build(artwork, template_summary(artwork), False, image_path),
                            content_type=content_type)
    response['Content-Disposition'] = f'attachment; filename="{slugify(artwork.title) or "artwork"}.{kind}"'
    return response