from django.db import models
from django.conf import settings
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
import io
import os
import base64

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

# AES密钥（16字节）
AES_KEY = b'\x8f\x1a\x9c\x8e\x1b\x8d\x1e\x8f\x1a\x9c\x8e\x1b\x8d\x1e\x8f\x1a'  # 自动生成的16字节密钥

def pad(s):
    """填充函数"""
    return s + (16 - len(s.encode('utf-8')) % 16) * chr(16 - len(s.encode('utf-8')) % 16)

def unpad(s):
    """去填充函数"""
    return s[:-ord(s[len(s)-1:])]

def aes_encrypt_text(text):
    """AES加密文本"""
    cipher = AES.new(AES_KEY, AES.MODE_ECB)
    padded = pad(text)
    encrypted = cipher.encrypt(padded.encode('utf-8'))
    return base64.b64encode(encrypted).decode('utf-8')

def aes_decrypt_text(enc_text):
    """AES解密文本"""
    cipher = AES.new(AES_KEY, AES.MODE_ECB)
    decrypted = cipher.decrypt(base64.b64decode(enc_text))
    return unpad(decrypted.decode('utf-8'))

# AES加密
def aes_encrypt_image(image_bytes, key):
    cipher = AES.new(key, AES.MODE_EAX)
    ciphertext, tag = cipher.encrypt_and_digest(image_bytes)
    return cipher.nonce + tag + ciphertext

def aes_decrypt_image(encrypted_bytes, key):
    nonce = encrypted_bytes[:16]
    tag = encrypted_bytes[16:32]
    ciphertext = encrypted_bytes[32:]
    cipher = AES.new(key, AES.MODE_EAX, nonce=nonce)
    return cipher.decrypt_and_verify(ciphertext, tag)

# 修改ImageField的保存和读取逻辑
from django.core.files.base import ContentFile
from django.db.models.fields.files import ImageFieldFile

class EncryptedImageFieldFile(ImageFieldFile):
    def save(self, name, content, save=True):
        # 只对图片内容加密
        encrypted = aes_encrypt_image(content.read(), AES_KEY)
        content = ContentFile(encrypted)
        super().save(name, content, save)

    def open(self, mode='rb'):
        file = super().open(mode)
        encrypted = file.read()
        file.close()
        decrypted = aes_decrypt_image(encrypted, AES_KEY)
        # 返回一个BytesIO对象，模拟文件
        return io.BytesIO(decrypted)

class EncryptedImageField(models.ImageField):
    attr_class = EncryptedImageFieldFile

class UserProfile(models.Model):
    username = models.CharField(max_length=20, unique=True)
    password = models.CharField(max_length=128)
    email = models.EmailField(max_length=50, unique=True)
    phone = models.CharField(max_length=20, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    # 百度人脸库ID，用于后续人脸识别
    face_id = models.CharField(max_length=128, blank=True, null=True)
    # 主要头像图片
    face_image = EncryptedImageField(upload_to=user_face_path, blank=True, null=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)  # 新增用户头像字段
    # 用户权限：0-普通用户，1-维修工，2-管理员
    permission = models.IntegerField(choices=[
        (0, '普通用户'),
        (1, '维修工'),
        (2, '管理员')
    ], default=0)
    
    def __str__(self):
        return self.username

# 用户人脸图片表，一个用户可以有多张人脸图片
class UserFaceImage(models.Model):
    user = models.ForeignKey(UserProfile, related_name='face_images', on_delete=models.CASCADE)
    image = EncryptedImageField(upload_to=user_face_path)
    face_token = models.CharField(max_length=128, blank=True, null=True)  # 百度人脸识别返回的face_token
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username}'s face image {self.id}"

class SystemLog(models.Model):
    user = models.ForeignKey(UserProfile, related_name='logs', on_delete=models.CASCADE,null=True,blank=True)  # 关联用户ID
    level = models.CharField(max_length=20, choices=[
        ('info', 'Info'),
        ('warning', 'Warning'),
        ('error', 'Error'),
    ], default='info')  # 日志级别
    ip_address = models.GenericIPAddressField(null=True, blank=True)  # 操作IP地址
    action = models.CharField(max_length=100)  # 描述用户操作
    timestamp = models.DateTimeField(auto_now_add=True)  # 操作时间
    details = models.TextField(blank=True, null=True)  # 其他操作细节 
    alert_event = models.ForeignKey('AlertEvent', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.action} at {self.timestamp}"

# 车辆轨迹点模型
class TrajectoryPoint(models.Model):
    lat = models.FloatField()
    lon = models.FloatField()
    time = models.DateTimeField()
    car = models.CharField(max_length=32)
    head = models.FloatField(null=True, blank=True)
    tflag = models.CharField(max_length=16, null=True, blank=True)
    status = models.CharField(max_length=16, null=True, blank=True)

    def __str__(self):
        return f"{self.car} @ {self.time} ({self.lat}, {self.lon})"

class AlertEvent(models.Model):
    alert_time = models.DateTimeField()
    alert_type = models.CharField(max_length=50)
    status = models.CharField(max_length=20)
    related_data = models.JSONField()
    user = models.ForeignKey('UserProfile', on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        db_table = 'web_alertevent'

class UserAvatar(models.Model):
    """用户头像存储表 - 存储在云数据库中"""
    user = models.OneToOneField(UserProfile, on_delete=models.CASCADE, related_name='db_avatar')
    avatar_data = models.BinaryField()  # 存储头像的二进制数据
    file_name = models.CharField(max_length=255)  # 原始文件名
    content_type = models.CharField(max_length=100)  # 文件类型 (image/jpeg, image/png等)
    file_size = models.IntegerField(default=0)  # 文件大小（字节），加默认值
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'web_useravatar'
    
    def __str__(self):
        return f"{self.user.username}'s avatar"