from django.urls import path
from . import views

urlpatterns = [
    path('road/upload', views.upload_image),
    path('history/list', views.history_get),
    path('history/delete', views.history_delete),
    path('heatmap/', views.heatmap_data),
    path('week_flow/', views.week_flow),
    path('road_distance_type/', views.road_distance_type),
    path('road_avg_speed/', views.road_avg_speed),
]