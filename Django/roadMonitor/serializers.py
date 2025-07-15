import os
from django.conf import settings
from requests import request
from rest_framework import serializers
from .models import roadRecord

class RoadRecordSerializer(serializers.ModelSerializer):

    class Meta:
        model = roadRecord
        fields = ['disease_id', 'road_id', 'disease_type', 'severity']
        extra_kwargs = {
            'road_id': {'required': True, 'min_value': 1},
            'disease_type': {'required': True},
            'severity': {'required': True},
            'path': {'required': True, 'max_length': 255},
        }

    def validate_length(self, value):
        """验证裂缝长度必须为正数"""
        if value <= 0:
            raise serializers.ValidationError("裂缝长度必须大于0")
        return value

    def validate_area(self, value):
        """验证病害面积必须为正数"""
        if value <= 0:
            raise serializers.ValidationError("病害面积必须大于0")
        return value

    def to_representation(self, instance):
        """自定义序列化输出格式"""
        data = super().to_representation(instance)
        
        # 替换数值为可读标签
        data['disease_type'] = instance.get_disease_type_display()
        data['severity'] = instance.get_severity_display()
        url = os.path.join(settings.MEDIA_URL, 'road', 'results', instance.path)
        # 添加额外信息
        data['detection_date'] = instance.detection_time.strftime("%Y-%m-%d")
        data['url'] = 'http://localhost:8000' + url
        
        return data