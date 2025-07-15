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
