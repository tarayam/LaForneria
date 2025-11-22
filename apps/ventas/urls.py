from django.urls import path
from . import views

urlpatterns = [
    path("", views.pos_ventas, name="pos_ventas"),  # /ventas/
    path("api/checkout/", views.checkout, name="ventas_checkout"),
]
