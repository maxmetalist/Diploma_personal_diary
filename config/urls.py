from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

from diary.views import home

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", home, name="home"),
    path("diary/", include("diary.urls")),
    path("catalog/", RedirectView.as_view(pattern_name="diary:home")),
    path("planner/", include("planner.urls")),
    path("alarm/", include("alarm.urls")),
    path("accounts/", include("users.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
