from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path("admin/", admin.site.urls),

    # Web
    path("", include("products.urls")),
    path("", include("orders.urls")),
    path("", include("users.urls")),

    # REST API
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/", include("products.urls", namespace="api-products")),
    path("api/", include("orders.urls", namespace="api-orders")),
    path("api/", include("users.urls", namespace="api-users")),

    # GraphQL
    path("", include("graphql_app.urls")),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
