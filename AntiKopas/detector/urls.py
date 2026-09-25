from django.urls import path

from .views import (
    health_check,
    detect_similarity,
    download_report
)


urlpatterns = [
    path("health/", health_check),
    path("detect/", detect_similarity),
    path(
        "reports/<str:filename>/",
        download_report
    ),
]