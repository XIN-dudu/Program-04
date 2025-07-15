from django.urls import path
from . import views

urlpatterns = [
    path('login', views.login),
    path('user/<int:id>', views.user_detail),
    path('register', views.register),
    path('send_email_code', views.send_email_code),
    path('email_login', views.email_login),
    path('face_recognition', views.face_recognition),
    path('liveness_detection', views.liveness_detection),
    path('liveness_check', views.liveness_check),
    path('api/liveness_check', views.liveness_check),
    path('click_captcha/', views.click_captcha),
    path('click_captcha/verify/', views.click_captcha_verify),
    path('update_profile/', views.update_profile),
    path('upload_avatar/', views.upload_avatar),
    path('check_email_available/', views.check_email_available),
    path('user_list/', views.user_list),
    path('update_permission/', views.update_permission),
    path('delete_user/', views.delete_user),
    path('points/', views.points_api),
    path('face_verify_one_to_one/', views.face_verify_one_to_one),
    path('logs/', views.log_list),
    path('user/profile/', views.current_user_profile),
    path('avatar/<str:username>/', views.get_avatar),
    path('liveness_and_face_verify/', views.liveness_and_face_verify),
] 