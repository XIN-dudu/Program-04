from django.urls import path
from . import views

urlpatterns = [
    path('road/upload', views.upload_image),
    path('history/list', views.history_get),
    path('history/<int:diseaseId>/delete', views.history_delete),
    path('road/streamFrame', views.upload_stream),
    path('heatmap/', views.heatmap_data),
    path('week_flow/', views.week_flow),
    path('road_distance_type/', views.road_distance_type),
    path('road_avg_speed/', views.road_avg_speed),
    path('heatmap_clustered/', views.heatmap_clustered, name='heatmap_clustered'),
    path('weekly_flow_time_distribution/', views.weekly_flow_time_distribution),
    path('od_analysis/', views.od_analysis),
    path('weather_flow_analysis/', views.weather_flow_analysis),
    path('weather_flow_analysis_fast/', views.weather_flow_analysis_fast),
    path('weather_flow_analysis_preprocessed/', views.weather_flow_analysis_preprocessed),
    path('occupied_taxi_count/', views.occupied_taxi_count),
    path('occupied_taxi_count_preprocessed/', views.occupied_taxi_count_preprocessed),
    path('trip_distance_analysis/', views.trip_distance_analysis),
    path('tasks/<int:task_id>/assign/', views.assign_task),
    path('my_tasks/', views.my_tasks),
    path('tasks/<int:task_id>/complete/', views.complete_task),
    path('tasks/<int:task_id>/images/', views.get_task_images),
    path('tasks/image/<int:image_id>/delete/', views.delete_task_image),
    path('tasks/<int:task_id>/mark_finished/', views.mark_finished),
    path('test', views.test_get),
]