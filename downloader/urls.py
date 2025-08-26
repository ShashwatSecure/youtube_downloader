from django.urls import path
from . import views

urlpatterns = [
    path('', views.playlist_view, name='playlist_view'),
    path('download_video/', views.download_video, name='download_video'),
    path('get_progress/<path:video_url>/', views.get_progress, name='get_progress'),
    path('play_video/', views.play_video, name='play_video'),
]