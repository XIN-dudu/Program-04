from django.db import models
from django.conf import settings
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
import io
import os

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

# AES密钥（16/24/32字节），实际部署时请安全存储
AES_KEY = b'\x8f\x1a\x9c\x8e\x1b\x8d\x1e\x8f\x1a\x9c\x8e\x1b\x8d\x1e\x8f\x1a'  # 自动生成的16字节密钥
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
