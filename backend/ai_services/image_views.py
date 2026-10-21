"""Image analysis endpoint (in its own module because it is the longest view)."""

import io
import uuid

from django.core.files.base import ContentFile
from django.db import OperationalError, transaction
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from gallery.models import Artwork

from .image_analysis import ImageRejected, analyze_artwork, load_image
from .models import AIAnalysis
from .serializers import ImageUploadSerializer
from .views import AiAnonThrottle, AiUserThrottle, _favorite_ids, _serialize


class AnalyzeImageView(GenericAPIView):
    """POST /api/ai/analyze-image/ as multipart form data with a file field named 'image'."""

    serializer_class = ImageUploadSerializer  # also lets the browsable API show a file picker
    permission_classes = [AllowAny]
    throttle_classes = [AiAnonThrottle, AiUserThrottle]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        serializer = ImageUploadSerializer(data=request.data)
        if not serializer.is_valid():
            first_message = next(iter(serializer.errors.values()))[0]
            return Response({'detail': str(first_message)}, status=status.HTTP_400_BAD_REQUEST)

        try:
            image = load_image(serializer.validated_data['image'])
        except ImageRejected as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        result = analyze_artwork(image)
        similar = result['similar'][:3]

        # Save a clean re-encoded copy (no metadata) under a random name
        buffer = io.BytesIO()
        image.save(buffer, 'JPEG', quality=88)
        analysis = AIAnalysis(
            user=request.user if request.user.is_authenticated else None,
            predicted_category=result['category'] or '',
            predicted_style=result['style'] or '',
            dominant_colors=result['dominant_colors'],
            source='fallback' if result['is_demo'] else 'computer_vision',
            notes=result['notice'])
        analysis.image.save(f'{uuid.uuid4().hex}.jpg', ContentFile(buffer.getvalue()), save=False)

        try:
            with transaction.atomic():  # all database writes succeed together or not at all
                analysis.save()
                analysis.similar_artworks.set([artwork for _, artwork in similar])
        except OperationalError:
            analysis.image.delete(save=False)  # do not leave an orphan file behind
            return Response({'detail': 'The server is busy right now. Please try again in a moment.'},
                            status=status.HTTP_503_SERVICE_UNAVAILABLE)

        similar_data = _serialize([artwork for _, artwork in similar], request,
                                  _favorite_ids(request.user))
        for item, (share, _) in zip(similar_data, similar):
            item['match_percent'] = int(round(100 * share))

        return Response({
            'id': analysis.id,
            'image_url': request.build_absolute_uri(analysis.image.url),
            'category': result['category'],
            'style': result['style'],
            'style_label': dict(Artwork.STYLE_CHOICES).get(result['style']),
            'dominant_colors': result['dominant_colors'],
            'palette': result['palette'],
            'similar_artworks': similar_data,
            'source': analysis.source,
            'is_demo_result': result['is_demo'],
            'methods': result['methods'],
            'notice': result['notice'],
        })


        