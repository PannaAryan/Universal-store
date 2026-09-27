from django.urls import path

from . import views_storefront as v

app_name = "storefront"

urlpatterns = [
    path("<slug:slug>/", v.home, name="home"),
    path("<slug:slug>/p/<slug:product_slug>/", v.product, name="product"),
    path("<slug:slug>/bag/", v.cart, name="cart"),
    path("<slug:slug>/bag/add/", v.cart_add, name="cart_add"),
    path("<slug:slug>/checkout/", v.checkout, name="checkout"),
    path("<slug:slug>/checkout/verify/", v.verify, name="verify"),
    path("<slug:slug>/order/<str:number>/", v.order, name="order"),
    path("<slug:slug>/track/", v.track, name="track"),
]
