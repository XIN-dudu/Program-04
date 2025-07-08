from django.db import models

# Create your models here.

def user_face_path(instance, filename):
    # 兼容UserProfile和UserFaceImage
    if hasattr(instance, 'username'):
        username = instance.username
    elif hasattr(instance, 'user') and hasattr(instance.user, 'username'):
        username = instance.user.username
    else:
        username = 'unknown'
    return f'face_images/{username}/{filename}'

class UserProfile(models.Model):
    username = models.CharField(max_length=20, unique=True)
    password = models.CharField(max_length=128)
    email = models.EmailField(max_length=50, unique=True)
    phone = models.CharField(max_length=20, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    # 百度人脸库ID，用于后续人脸识别
    face_id = models.CharField(max_length=128, blank=True, null=True)
    # 主要头像图片
    face_image = models.ImageField(upload_to=user_face_path, blank=True, null=True)
    
    def __str__(self):
        return self.username

# 用户人脸图片表，一个用户可以有多张人脸图片
class UserFaceImage(models.Model):
    user = models.ForeignKey(UserProfile, related_name='face_images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to=user_face_path)
    face_token = models.CharField(max_length=128, blank=True, null=True)  # 百度人脸识别返回的face_token
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username}'s face image {self.id}"
