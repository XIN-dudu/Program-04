from django.urls import path
from . import views

urlpatterns = [
    path('road/upload', views.upload_image),
    path('history/list', views.history_get),
    path('history/<int:diseaseId>/delete', views.history_delete),
    path('heatmap/', views.heatmap_data),
    path('week_flow/', views.week_flow),
    path('road_distance_type/', views.road_distance_type),
    path('road_avg_speed/', views.road_avg_speed),
    path('heatmap_clustered/', views.heatmap_clustered, name='heatmap_clustered'),
    path('weekly_flow_time_distribution/', views.weekly_flow_time_distribution),
    path('od_analysis/', views.od_analysis),
    path('weather_flow_analysis/', views.weather_flow_analysis),
    path('test', views.test_get),
]