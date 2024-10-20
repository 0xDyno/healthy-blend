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
    UserViewSet, IngredientViewSet, ProductViewSet, OrderViewSet, HistoryViewSet,
    home, user_login, user_logout, custom_meal, user_management,
    product_management, ingredient_management, orders, cart,
    order_confirmation, ingredient_detail, checkout
)

# Создаем роутер для API
router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'ingredients', IngredientViewSet)
router.register(r'products', ProductViewSet)
router.register(r'orders', OrderViewSet)
router.register(r'history', HistoryViewSet)

urlpatterns = [
    # Административная панель Django
    path('admin/', admin.site.urls),

    # Основные страницы веб-приложения
    path('', home, name='home'),
    path('login/', user_login, name='login'),
    path('logout/', user_logout, name='logout'),
    path('custom-meal/', custom_meal, name='custom_meal'),
    path('user-management/', user_management, name='user_management'),
    path('product-management/', product_management, name='product_management'),
    path('ingredient-management/', ingredient_management, name='ingredient_management'),
    path('orders/', orders, name='orders'),
    path('cart/', cart, name='cart'),
    path('checkout/', checkout, name='checkout'),
    path('order-confirmation/<int:order_id>/', order_confirmation, name='order_confirmation'),
    path('ingredient/<int:ingredient_id>/', ingredient_detail, name='ingredient_detail'),
    path('checkout/', checkout, name='checkout'),
    # API URLs
    path('api/', include(router.urls)),
    path('api-auth/', include('rest_framework.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
