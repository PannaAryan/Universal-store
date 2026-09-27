from django.conf import settings
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.static import serve

admin.site.site_header = f"{settings.BRAND['name']} admin"
admin.site.site_title = settings.BRAND["name"]

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("accounts.urls")),
    path("dashboard/", include("stores.urls_dashboard")),
    path("s/", include("stores.urls_storefront")),
    path("", include("core.urls")),
]

if settings.SERVE_MEDIA:
    # Uploaded images. On Vercel these live in /tmp and are lost on redeploys; use
    # object storage (Vercel Blob, S3, Cloudinary) for permanent uploads.
    urlpatterns.insert(0, re_path(r"^media/(?P<path>.*)$", serve, {"document_root": settings.MEDIA_ROOT}))

handler404 = "core.views.not_found"
