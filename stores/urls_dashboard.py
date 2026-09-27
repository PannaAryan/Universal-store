from django.urls import path

from . import views_dashboard as v

app_name = "dashboard"

urlpatterns = [
    path("", v.home, name="home"),
    path("welcome/", v.onboarding, name="onboarding"),
    path("products/", v.products, name="products"),
    path("products/new/", v.product_edit, name="product_add"),
    path("products/<int:pk>/", v.product_edit, name="product_edit"),
    path("products/<int:pk>/delete/", v.product_delete, name="product_delete"),
    path("ai/generate/", v.ai_generate, name="ai_generate"),
    path("orders/", v.orders, name="orders"),
    path("orders/new/", v.order_add, name="order_add"),
    path("orders/<str:number>/", v.order_detail, name="order_detail"),
    path("customers/", v.customers, name="customers"),
    path("coupons/", v.coupons, name="coupons"),
    path("coupons/<int:pk>/toggle/", v.coupon_toggle, name="coupon_toggle"),
    path("analytics/", v.analytics, name="analytics"),
    path("settings/", v.store_settings, name="settings"),
    path("billing/", v.billing, name="billing"),
]
