from django.urls import path
from . import views

urlpatterns = [
    path('', views.index),
    path('api/search/', views.api_search),
    path('api/routes/', views.api_routes),
    path('api/stops/', views.api_stops),
    path('api/live/', views.api_live),
    path('api/update-location/', views.api_update_location),
    path('api/stop-coords/', views.api_stop_coords),
    path('api/weather/', views.api_weather),        # OpenWeatherMap
    path('api/road-route/', views.api_road_route),  # OpenRouteService
]
