from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from core import views as core_views

urlpatterns = [
    path("django-admin/", admin.site.urls),
    path("", core_views.home, name="home"),
    path("apply/", core_views.apply, name="apply"),
    path("admin-panel/", include("core.urls")),
    path("api/", include("finance.urls")),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
