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
    checkout, add_to_cart, remove_from_cart, update_order_status, order_confirmation, ingredient_detail, get_ingredients,
    get_custom_meal_summary, add_ingredient_to_custom_meal, remove_ingredient_from_custom_meal, add_custom_meal_to_order
)

# Создаем роутер для API
router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'ingredients', IngredientViewSet)
router.register(r'products', ProductViewSet)
router.register(r'orders', OrderViewSet)
router.register(r'history', HistoryViewSet)

router = DefaultRouter()
router.register(r'products', ProductViewSet)

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

    # Функции для работы с корзиной
    path('add-to-cart/', add_to_cart, name='add_to_cart'),
    path('remove-from-cart/', remove_from_cart, name='remove_from_cart'),
    path('checkout/', checkout, name='checkout'),
    path('order-confirmation/<int:order_id>/', order_confirmation, name='order_confirmation'),

    # AJAX-запрос для обновления статуса заказа
    path('update-order-status/', update_order_status, name='update_order_status'),

    # API URLs
    path('api/', include(router.urls)),
    path('api-auth/', include('rest_framework.urls')),
    path('api/products/custom/', ProductViewSet.as_view({'post': 'custom'}), name='custom_product'),
    path('api/orders/current/', OrderViewSet.as_view({'get': 'current'}), name='current_order'),
    path('api/orders/<int:pk>/update-status/', OrderViewSet.as_view({'post': 'update_status'}), name='update_order_status'),

    path('custom-meal/', custom_meal, name='custom_meal'),
    path('ingredient/<int:ingredient_id>/', ingredient_detail, name='ingredient_detail'),
    path('api/ingredients/', get_ingredients, name='get_ingredients'),
    path('api/custom-meal-summary/', get_custom_meal_summary, name='get_custom_meal_summary'),
    path('api/add-ingredient-to-custom-meal/', add_ingredient_to_custom_meal, name='add_ingredient_to_custom_meal'),

    path('api/remove-ingredient-from-custom-meal/', remove_ingredient_from_custom_meal, name='remove_ingredient_from_custom_meal'),
    path('api/add-custom-meal-to-order/', add_custom_meal_to_order, name='add_custom_meal_to_order'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
