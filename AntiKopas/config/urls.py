from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from detector.views import download_media

import os

# Arahkan tombol View Site secara dinamis ke root frontend host ('/'), atau ikuti env FRONTEND_URL.
admin.site.site_url = os.getenv("FRONTEND_URL", "/")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("detector.urls")),
    path("api/auth/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("media/<path:filename>", download_media, name="protected_media"),
]
