from django.urls import path
from . import views

urlpatterns = [
    path('road/upload', views.upload_image),
    path('history/list', views.history_get),
    path('history/video', views.history_video),
    path('history/delete', views.history_delete),
]
