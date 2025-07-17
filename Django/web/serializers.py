from rest_framework import serializers
from .models import UserProfile, UserFaceImage , SystemLog


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
class LogSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    alert_event_id = serializers.SerializerMethodField()
    alert_event_video_url = serializers.SerializerMethodField()

    def get_alert_event_id(self, obj):
        return obj.alert_event.id if obj.alert_event else None

    def get_alert_event_video_url(self, obj):
        if obj.alert_event and obj.alert_event.video:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.alert_event.video.url)
            return obj.alert_event.video.url
        return None

    class Meta:
        model = SystemLog
        fields = ['id','level','user', 'ip_address', 'action', 'details', 'timestamp', 'alert_event_id', 'alert_event_video_url']
        read_only_fields = ['id', 'timestamp']

    # def create(self, validated_data):
    #     # 可以在这里添加日志创建时的额外逻辑
    #     return super().create(validated_data)