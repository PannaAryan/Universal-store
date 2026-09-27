from django.urls import path

from . import views

app_name = "core"

urlpatterns = [
    path("", views.home, name="home"),
    path("features/", views.features, name="features"),
    path("ai-snap-and-sell/", views.snap_and_sell, name="snap"),
    path("ai-snap-and-sell/try/", views.snap_demo, name="snap_demo"),
    path("pricing/", views.pricing, name="pricing"),
    path("compare/", views.compare, name="compare"),
    path("about/", views.about, name="about"),
    path("investors/", views.investors, name="investors"),
    path("contact/", views.contact, name="contact"),
    path("help/", views.help_center, name="help"),
    path("status/", views.status, name="status"),
    path("legal/<slug:page>/", views.legal, name="legal"),
    path("newsletter/", views.newsletter, name="newsletter"),
]
