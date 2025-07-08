from django.urls import path
from . import views

urlpatterns = [
    path('login', views.login),
    path('user/<int:id>', views.user_detail),
    path('register', views.register),
    path('send_email_code', views.send_email_code),
    path('email_login', views.email_login),
]
