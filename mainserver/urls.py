
from django.contrib import admin
from django.urls import path,include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)
urlpatterns = [
    path('/', admin.site.urls),
    path('accounting/', include('accounting.urls')),
    path('actors/', include('actors.urls')),
    path('authentication/', include('authentication.urls')),
    path('core/', include('core.urls')),
    path('crm/', include('crm.urls')),
     path('master/', include('master.urls')),
    path('operations/', include('operations.urls')),
    path('pickup/', include('pickup.urls')),
    path('purchase/', include('purchase.urls')),
    path('sales/', include('sales.urls')),
    path('warehouse/', include('warehouse.urls')),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),#the normal api docs path
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),# Swagger UI
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),   # Redoc UI (optional)
    path("auth/", include("djoser.urls")),
    path("auth/", include("djoser.urls.jwt")),
]
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
