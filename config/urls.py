"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from core.views import (
    api_get_orders, api_get_all_products, api_get_ingredient, api_get_all_ingredients, api_get_order, api_update_order,
    home, user_login, user_logout, custom_meal, custom_add, cart, checkout, last_order,
    order_management, product_management, ingredient_management)

urlpatterns = [
    path('admin/', admin.site.urls),

    path('', home, name='home'),
    path('login/', user_login, name='login'),
    path('logout/', user_logout, name='logout'),

    path('custom-meal/', custom_meal, name='custom_meal'),
    path('ingredient/<int:ingredient_id>/', custom_add, name='ingredient_detail'),
    path('cart/', cart, name='cart'),
    path('checkout/', checkout, name='checkout'),
    path('last-order/', last_order, name='last_order'),

    path('order-management/', order_management, name='order_management'),
    path('ingredient-management/', ingredient_management, name='ingredient_management'),
    path('product-management/', product_management, name='product_management'),
    path('checkout/', checkout, name='checkout'),

    # API URLs
    path('api/get/products/', api_get_all_products),
    path('api/get/ingredient/<int:pk>/', api_get_ingredient),
    path('api/get/ingredients/', api_get_all_ingredients),
    path('api/get/order/<int:pk>/', api_get_order),
    path('api/get/orders/', api_get_orders),
    path('api/update/order/<int:pk>/', api_update_order),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
