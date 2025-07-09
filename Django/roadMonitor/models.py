from django.db import models

# Create your models here.

class alarmEvents(models.Model):
    alter_id = models.AutoField(primary_key=True)
    alter_time = models.DateTimeField(auto_now_add=True)
    ALERT_TYPE_CHOICES = [
        ('illegal_intrusion', '非法入侵'),
        ('deep_fake', '深度伪造'),
        ('road_disease', '路面病害'),
        ('abnormal_data', '异常数据'),
    ]
    alert_type = models.CharField(max_length=20, choices=ALERT_TYPE_CHOICES, null=False, blank=False)
    STATUS_CHOICES = [
        ('NEW', '新建'),
        ('PROCESSING', '处理中'),
        ('RESOLVED', '已处理'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='NEW')
    related_date = models.JSONField(
        verbose_name='关联日期数据',
        null=True,
        blank=True,
        default=dict  # 避免空值导致的存储问题
    )
    user_id = models.ForeignKey("web.UserProfile",on_delete=models.CASCADE)

# class roadRecord(models.Model):
#     disease_id = models.AutoField(primary_key=True)
#     detection_time = models.DateTimeField(auto_now_add=True)
#     DISEASE_TYPE_CHOICES = [
#         (1, '纵向裂缝'),
#         (2, '横向裂缝'),
#         (3, '龟裂'),
#         (4, '坑洼'),
#     ]
#     disease_type = models.IntegerField(choices=DISEASE_TYPE_CHOICES, null=False, blank=False)
#     length = models.FloatField()
#     area = models.FloatField()
#     SEVERITY_CHOICES = [
#         (1, 'LOW'),
#         (2, 'MEDIUM'),
#         (3, 'HIGH'),    
#     ]
#     severity = models.IntegerField(choices=SEVERITY_CHOICES, null=False, blank=False)
#     path = models.CharField(max_length=255)
#     position = models.PointField(
#         verbose_name='地理位置',
#         srid=4326,  # 使用WGS84坐标系
#         null=False,
#         blank=False,
#         spatial_index=True  # 创建空间索引
#     )




