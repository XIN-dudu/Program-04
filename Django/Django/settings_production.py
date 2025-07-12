"""
Django production settings for Django project.
"""

import os
from pathlib import Path
from .settings import *

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-@l+)l^ure&c4_0$4(*@e4q&(il1a@*s)3dw4#3^p2orjo0k9+c')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

# 替换为您的云服务器IP或域名

ALLOWED_HOSTS = ['971646.xyz', 'www.971646.xyz', '120.46.211.91', 'localhost']


# 数据库配置（使用环境变量）
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.environ.get('DB_NAME', 'program-04'),
        'USER': os.environ.get('DB_USER', 'root'),
        'PASSWORD': os.environ.get('DB_PASSWORD', 'Xin123456'),
        'HOST': os.environ.get('DB_HOST', '122.9.42.250'),
        'PORT': os.environ.get('DB_PORT', '3306'),
    }
}

# 静态文件配置
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# 媒体文件配置
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# CORS配置（生产环境）
CORS_ALLOWED_ORIGINS = [
    "http://your-server-ip",
    "http://your-domain.com",
    "https://your-domain.com",
]

# 安全设置
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# 会话安全
SESSION_COOKIE_SECURE = True

CSRF_COOKIE_SECURE = True 

CORS_ALLOW_CREDENTIALS = True
CORS_ALLOWED_ORIGINS = [
    "http://971646.xyz",
    "https://971646.xyz",
    "http://www.971646.xyz",
    "https://www.971646.xyz",
]
12
CSRF_TRUSTED_ORIGINS = [
    "http://971646.xyz",
    "https://971646.xyz",
    "http://www.971646.xyz",
    "https://www.971646.xyz",
]

