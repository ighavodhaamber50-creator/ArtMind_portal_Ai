"""Serializer that validates the uploaded file (used by the image analysis endpoint)."""

import os

from rest_framework import serializers

MAX_UPLOAD_BYTES = 5 * 1024 * 1024
ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp'}


class ImageUploadSerializer(serializers.Serializer):
    image = serializers.ImageField(error_messages={
        'required': 'Please choose an image to upload.',
        'empty': 'That file is empty. Please choose another image.',
        'invalid_image': 'That file is not a valid image. Please upload a JPG, PNG or WEBP picture.',
    })

    def validate_image(self, upload):
        if upload.size > MAX_UPLOAD_BYTES:
            raise serializers.ValidationError('That image is larger than 5 MB. Please upload a smaller file.')
        if os.path.splitext(upload.name)[1].lower() not in ALLOWED_EXTENSIONS:
            raise serializers.ValidationError('Please upload a JPG, PNG or WEBP image.')
        return upload