from django.urls import path
from . import views

urlpatterns = [
    path('login', views.login),
    path('user/<int:id>', views.user_detail),
    path('register', views.register),
    path('send_email_code', views.send_email_code),#发送验证码
    path('email_login', views.email_login),#邮箱登录
    path('face_recognition', views.face_recognition),
    path('liveness_detection', views.liveness_detection),
]
