# views.py

import json
import logging
from datetime import timedelta

from django.core.exceptions import ValidationError
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_POST
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import User, Ingredient, Product, Order, History
from .serializers import UserSerializer, IngredientSerializer, ProductSerializer, OrderSerializer, HistorySerializer
from .forms import LoginForm
from . import utils

logger = logging.getLogger(__name__)


class IsAdminUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'admin'


class IsManagerUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'manager'


class IsTableUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'table'


class IsKitchenUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'kitchen'


# API ViewSets

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdminUser]


class IngredientViewSet(viewsets.ModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = [IsAdminUser | IsManagerUser]

    @action(detail=True, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def get_ingredient(self, request, pk=None):
        ingredient = self.get_object()

        data = utils.get_ingredient_data(ingredient)

        return Response(data)

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def all_ingredients(self, request):
        ingredients = Ingredient.objects.filter()
        data = [utils.get_ingredient_data(ingredient) for ingredient in ingredients]
        return Response(data)


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAdminUser | IsManagerUser]

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def all_products(self, request):
        products = Product.objects.filter(is_official=True)
        data = []
        for product in products:
            product_info = {'id': product.id,
                            'product_type': product.product_type,
                            'name': product.name,
                            'description': product.description,
                            'image': product.image.url if product.image else None,
                            'weight': product.weight,
                            'price': product.get_selling_price(),
                            'ingredients': [],
                            'nutritional_value': product.nutritional_value.to_dict()}
            for pi in product.productingredient_set.all():
                ingredient_info = {'id': pi.ingredient.id,
                                   'name': pi.ingredient.name,
                                   'weight_grams': pi.weight_grams,
                                   'nutritional_value': pi.ingredient.nutritional_value.to_dict(),
                                   'price': pi.ingredient.get_selling_price()}
                product_info.get("ingredients").append(ingredient_info)
            data.append(product_info)
        return Response(data)


class OrderViewSet(viewsets.ModelViewSet):
    """
    GET /api/orders/ - List orders (filtered based on user role)
    GET /api/orders/<id>/ - Retrieve a specific order (if the user has permission)
    POST /api/orders/ - Create a new order (admin only)
    PUT /api/orders/<id>/ - Update an order (admin only)
    PATCH /api/orders/<id>/ - Partially update an order (admin only)
    DELETE /api/orders/<id>/ - Delete an order (admin only)
    """
    queryset = Order.objects.all()
    serializer_class = OrderSerializer

    def get_queryset(self):
        user = self.request.user
        if user.role == 'admin':
            return Order.objects.all()
        elif user.role == 'manager':
            return Order.objects.filter(created_at__date=timezone.now().date())
        elif user.role == 'table':
            return Order.objects.filter(table=user, created_at__gte=timezone.now() - timedelta(hours=3))
        elif user.role == 'kitchen':
            return Order.objects.filter(
                order_status__in=['pending', 'processing'],
                payment_type__in=['card', 'qr']
            )
        return Order.objects.none()

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [permissions.IsAdminUser]
        return [permission() for permission in permission_classes]

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class HistoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = History.objects.all()
    serializer_class = HistorySerializer
    permission_classes = [IsAdminUser | IsManagerUser]

    def get_queryset(self):
        if self.request.user.role == 'table':
            return History.objects.filter(user=self.request.user)
        return super().get_queryset()


# Web Views

def user_login(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('home')
    else:
        form = LoginForm()
    return render(request, 'base/login.html', {'form': form})


@login_required
def user_logout(request):
    logout(request)
    return redirect('login')


@login_required
def home(request):
    return render(request, 'base/home.html')


@login_required
def custom_meal(request):
    return render(request, 'client/custom_meal.html')


@login_required
def custom_add(request, ingredient_id):
    return render(request, 'client/custom_add.html', {'ingredient_id': ingredient_id})


@login_required
def cart(request):
    context = {
        'is_manager': request.user.role == 'manager'
    }
    return render(request, 'client/cart.html', context)


@login_required
def orders(request):
    if request.user.role not in ['admin', 'manager']:
        return redirect('home')
    return render(request, 'manage/orders.html')


@login_required
@require_POST
def checkout(request):
    try:
        data = json.loads(request.body)
        official_meals = data.get('officialMeals', [])
        custom_meals = data.get('customMeals', [])

        total_price = utils.big_validator(data)

        order = Order.objects.create(table=request.user, payment_type=data["payment_type"], price=round(total_price))

        utils.process_official_meal(official_meals, order)
        utils.process_custom_meal(custom_meals, order)

        return JsonResponse({'success': True, 'redirect_url': f'/'})
    except ValidationError as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
def product_management(request):
    if request.user.role not in ['admin', 'manager']:
        return redirect('home')
    # Implement product management logic here
    return render(request, 'manage/product_management.html')


@login_required
def ingredient_management(request):
    if request.user.role not in ['admin', 'manager']:
        return redirect('home')
    # Implement ingredient management logic here
    return render(request, 'manage/ingredient_management.html')


@login_required
def update_order_status(request):
    if request.user.role not in ['admin', 'manager']:
        return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)

    order_id = request.POST.get('order_id')
    new_status = request.POST.get('status')
    order = get_object_or_404(Order, id=order_id)
    order.order_status = new_status
    order.save()
    return JsonResponse({'success': True})
