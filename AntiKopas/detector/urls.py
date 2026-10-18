from django.urls import path

from .views import (
    health_check,
    register_user,
    analysis_list,
    analysis_detail,
    detect_similarity,
    download_report
)


urlpatterns = [
    path("health/", health_check),
    path("auth/register/", register_user),
    path("analyses/", analysis_list),
    path("analyses/<int:analysis_id>/", analysis_detail),
    path("detect/", detect_similarity),
    path(
        "reports/<str:filename>/",
        download_report
    ),
]
