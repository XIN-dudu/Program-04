import os
from django.conf import settings
from requests import request
from rest_framework import serializers
from .models import roadRecord


from rest_framework import serializers

class RoadSerializer(serializers.ModelSerializer):
    
    # 处理description字段
    description = serializers.JSONField()

    class Meta:
        model = roadRecord
        fields = ['road_id', 'description']
        
    def to_representation(self, instance):
        data = super().to_representation(instance)
        if isinstance(data['description'], list):
            for item in data['description']:
                # 将数字转换为文字描述
                severity_mapping = {v[0]: v[1] for v in roadRecord.SEVERITY_CHOICES}
                disease_type_mapping = {v[0]: v[1] for v in roadRecord.DISEASE_TYPE_CHOICES}
                item['severity'] = severity_mapping.get(item.get('severity'), 'UNKNOWN')
                item['disease_type'] = disease_type_mapping.get(item.get('disease_type'), 'UNKNOWN')
                url = os.path.join(settings.MEDIA_URL, 'road', item['url'])
                item['url'] = 'http://localhost:8000' + url
                
        return data

class RoadRecordSerializer(serializers.ModelSerializer):
    assigned_person_ids = serializers.SerializerMethodField()
    assignment_status = serializers.SerializerMethodField()

    class Meta:
        model = roadRecord
        fields = ['disease_id', 'road_id', 'disease_type', 'severity', 'assigned_person_ids', 'assignment_status']

        extra_kwargs = {
            'road_id': {'required': True, 'min_value': 1},
            'disease_type': {'required': True},
            'severity': {'required': True},
            'path': {'required': True, 'max_length': 255},
        }

    def get_assigned_person_ids(self, obj):
        return list(obj.assigned_workers.values_list('id', flat=True))

    def get_assignment_status(self, obj):
        request = self.context.get('request')
        if not request or not hasattr(request, 'session'):
            return None
        username = request.session.get('username')
        if not username:
            return None
        from web.models import UserProfile
        from .models import RepairAssignment
        try:
            user = UserProfile.objects.get(username=username)
            assignment = RepairAssignment.objects.get(road_record=obj, worker=user)
            return assignment.status
        except Exception:
            return None

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
        
        data['detection_date'] = instance.detection_time.strftime("%Y-%m-%d")

        if isinstance(data['description'], list):
            for item in data['description']:
                # 将数字转换为文字描述
                severity_mapping = {v[0]: v[1] for v in roadRecord.SEVERITY_CHOICES}
                disease_type_mapping = {v[0]: v[1] for v in roadRecord.DISEASE_TYPE_CHOICES}
                item['severity'] = severity_mapping.get(item.get('severity'), 'UNKNOWN')
                item['disease_type'] = disease_type_mapping.get(item.get('disease_type'), 'UNKNOWN')
                url = os.path.join(settings.MEDIA_URL, 'road', item['url'])
                item['url'] = 'http://localhost:8000' + url
                
        return data
