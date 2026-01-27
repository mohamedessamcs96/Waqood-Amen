"""
URL configuration for Gas Station Monitoring project.
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('apps.cars.urls')),
    path('api/', include('apps.vehicles.urls')),
]

# Serve static files
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Serve crop directories
urlpatterns += [
    re_path(r'^car_crops/(?P<path>.*)$', serve, {'document_root': settings.BASE_DIR / 'car_crops'}),
    re_path(r'^plate_crops/(?P<path>.*)$', serve, {'document_root': settings.BASE_DIR / 'plate_crops'}),
    re_path(r'^face_crops/(?P<path>.*)$', serve, {'document_root': settings.BASE_DIR / 'face_crops'}),
]
