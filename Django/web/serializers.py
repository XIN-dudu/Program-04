from rest_framework import serializers
from .models import UserProfile, UserFaceImage


class UserFaceImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserFaceImage
        fields = ['id', 'image', 'face_token', 'created_at']

class UserSerializer(serializers.ModelSerializer):
    face_images = UserFaceImageSerializer(many=True, read_only=True)
    
    class Meta:
        model = UserProfile
        fields = ['id', 'username', 'password', 'email', 'phone', 'created_at', 'face_image', 'face_id', 'face_images']
        extra_kwargs = {
            'password': {'write_only': True},
            'face_id': {'read_only': True}
        }