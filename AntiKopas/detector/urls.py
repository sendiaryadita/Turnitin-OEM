from django.urls import path
from .views import health_check, detect_similarity

urlpatterns = [
    path("health/", health_check),
    path("detect/", detect_similarity),
]