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

# 新增：维修完成图片表
class RepairCompletionImage(models.Model):
    assignment = models.ForeignKey(RepairAssignment, on_delete=models.CASCADE, related_name='completion_images')
    image = models.ImageField(upload_to='repair_complete/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Repair completion image for {self.assignment}"

# 新增：预处理数据表
class PreprocessedData(models.Model):
    """预处理数据表，用于存储预计算的统计数据"""
    
    DATA_TYPE_CHOICES = [
        ('weather_flow', '天气客流数据'),
        ('occupied_taxi', '载客出租车数据'),
        ('weekly_flow', '周客流量数据'),
        ('heatmap', '热力图数据'),
    ]
    
    data_type = models.CharField(max_length=20, choices=DATA_TYPE_CHOICES, verbose_name='数据类型')
    date = models.DateField(verbose_name='数据日期')
    hour = models.IntegerField(verbose_name='小时', null=True, blank=True)
    time_slot = models.CharField(max_length=20, verbose_name='时间段', null=True, blank=True)
    
    # 天气相关字段
    temperature = models.FloatField(verbose_name='温度', null=True, blank=True)
    humidity = models.FloatField(verbose_name='湿度', null=True, blank=True)
    wind_speed = models.FloatField(verbose_name='风速', null=True, blank=True)
    precip = models.FloatField(verbose_name='降水量', null=True, blank=True)
    
    # 流量相关字段
    passenger_flow = models.IntegerField(verbose_name='客流量', default=0)
    occupied_taxi_count = models.IntegerField(verbose_name='载客出租车数量', default=0)
    
    # 统计字段
    total_trips = models.IntegerField(verbose_name='总行程数', default=0)
    avg_speed = models.FloatField(verbose_name='平均速度', null=True, blank=True)
    
    # 元数据
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        db_table = 'preprocessed_data'
        unique_together = ('data_type', 'date', 'hour')
        indexes = [
            models.Index(fields=['data_type', 'date']),
            models.Index(fields=['data_type', 'date', 'hour']),
        ]
        verbose_name = '预处理数据'
        verbose_name_plural = '预处理数据'
    
    def __str__(self):
        return f"{self.get_data_type_display()} - {self.date} {self.hour:02d}:00" if self.hour else f"{self.get_data_type_display()} - {self.date}"