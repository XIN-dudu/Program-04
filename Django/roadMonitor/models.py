from django.db import models

# Create your models here.
class roadRecord(models.Model):
    disease_id = models.AutoField(primary_key=True)
    road_id = models.IntegerField(null=False)
    detection_time = models.DateTimeField(auto_now_add=True)
    DISEASE_TYPE_CHOICES = [
        (0, '无'),
        (1, '纵向裂缝'),
        (2, '横向裂缝'),
        (3, '龟裂'),
        (4, '坑洼'),
        (5, '修补')
    ]
    disease_type = models.IntegerField(choices=DISEASE_TYPE_CHOICES, null=False, blank=False)
    length = models.FloatField()
    area = models.FloatField()
    SEVERITY_CHOICES = [
        (0, 'SAFE'),
        (1, 'LOW'),
        (2, 'MEDIUM'),
        (3, 'HIGH'),    
    ]
    severity = models.IntegerField(choices=SEVERITY_CHOICES, null=False, blank=False)
    path = models.CharField(max_length=255, null=False, blank=False)
    FILE_TYPE_CHOICES = [
        (0, 'VIDEO'),
        (1, 'IMAGE'),   
    ]
    file_type = models.IntegerField(choices=FILE_TYPE_CHOICES, null=False, blank=False)
    description = models.JSONField(null=False, blank=False, default=dict)
    # 新增：多对多分配关系（通过中间表）
    assigned_workers = models.ManyToManyField('web.UserProfile', through='RepairAssignment', related_name='assigned_road_records', blank=True)

# 新增：任务分配中间表
class RepairAssignment(models.Model):
    road_record = models.ForeignKey(roadRecord, on_delete=models.CASCADE, related_name='assignments')
    worker = models.ForeignKey('web.UserProfile', on_delete=models.CASCADE, related_name='worker_assignments')
    assigned_time = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, default='pending')  # 可选：pending/finished等
    completion_image = models.CharField(max_length=255, blank=True, null=True)  # 新增：维修完成图片
    
    class Meta:
        unique_together = ('road_record', 'worker')
    
    def __str__(self):
        return f"{self.road_record.disease_id} -> {self.worker.username} ({self.status})"

class RepairCompletionImage(models.Model):
    assignment = models.ForeignKey('RepairAssignment', on_delete=models.CASCADE, related_name='completion_images')
    image = models.ImageField(upload_to='repair_complete/')
    uploaded_at = models.DateTimeField(auto_now_add=True)