from django.urls import path
from . import views

urlpatterns = [
    path('road/upload', views.upload_image),
    path('road/get_result', views.get_result),
    path('history/list', views.history_get),
    path('history/video', views.history_video),
    path('history/delete', views.history_delete),
    path('heatmap/', views.heatmap_data),
]
