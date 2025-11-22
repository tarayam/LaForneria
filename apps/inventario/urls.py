from django.urls import path
from . import views

urlpatterns = [
    path('', views.inventario_dashboard, name='inventario_dashboard'),
    path('api/ingreso/', views.inventario_dashboard, name='api_ingreso'),
    path('api/products/', views.product_search_api, name='api_products'),
]
