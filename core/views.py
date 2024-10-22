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
from .models import User, Ingredient, Product, Order, History, NutritionalValue
# from .serializers import UserSerializer, IngredientSerializer, ProductSerializer, OrderSerializer, HistorySerializer
from .forms import LoginForm
from . import utils

logger = logging.getLogger(__name__)


class IsAdminUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == "admin"


class IsManagerUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == "manager"


class IsTableUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == "table"


class IsKitchenUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == "kitchen"


# API ViewSets

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    # serializer_class = UserSerializer
    permission_classes = [IsAdminUser]


class IngredientViewSet(viewsets.ViewSet):
    http_method_names = ["get"]
    queryset = Ingredient.objects.all()
    # serializer_class = IngredientSerializer
    permission_classes = [IsAdminUser]

    @action(detail=True, methods=["get"], permission_classes=[permissions.IsAuthenticated])
    def get_ingredient(self, request, pk=None):
        ingredient = get_object_or_404(Ingredient, pk=pk)
        data = utils.get_ingredient_data(ingredient)

        return Response(data)

    @action(detail=False, methods=["get"], permission_classes=[permissions.IsAuthenticated])
    def all_ingredients(self, request):
        ingredients = Ingredient.objects.filter()
        data = [utils.get_ingredient_data(ingredient) for ingredient in ingredients]
        return Response(data)


class ProductViewSet(viewsets.ViewSet):
    queryset = Product.objects.all()
    # serializer_class = ProductSerializer
    permission_classes = [IsAdminUser]
    http_method_names = ["get"]

    @action(detail=False, methods=["get"], permission_classes=[permissions.IsAuthenticated])
    def all_products(self, request):
        products = Product.objects.filter(is_official=True)
        data = []
        for product in products:
            product_info = {"id": product.id,
                            "product_type": product.product_type,
                            "name": product.name,
                            "description": product.description,
                            "image": product.image.url if product.image else None,
                            "weight": product.weight,
                            "price": product.get_selling_price(),
                            "ingredients": [],
                            "nutritional_value": product.nutritional_value.to_dict()}
            for pi in product.productingredient_set.all():
                ingredient_info = {"id": pi.ingredient.id,
                                   "name": pi.ingredient.name,
                                   "weight_grams": pi.weight_grams,
                                   "nutritional_value": pi.ingredient.nutritional_value.to_dict(),
                                   "price": pi.ingredient.get_selling_price()}
                product_info.get("ingredients").append(ingredient_info)
            data.append(product_info)
        return Response(data)


class OrderViewSet(viewsets.ViewSet):
    queryset = Order.objects.all()
    permission_classes = [IsAdminUser]
    http_method_names = ["get"]

    @action(detail=False, methods=["get"], permission_classes=[permissions.IsAuthenticated])
    def get_orders(self, request):
        role = request.user.role
        now = timezone.now()
        data = []
        if role == "admin":
            orders_ = Order.objects.all().order_by("-created_at")
            data = utils.get_orders_full_info(orders_)
        if role == "manager":
            orders_ = Order.objects.filter(created_at__date=now.date()).order_by("-created_at")
            data = utils.get_orders_full_info(orders_)
        if role == "table":
            orders_ = Order.objects.filter(user=request.user, created_at__gte=now-timedelta(hours=3)).order_by("created_at")
            data = utils.get_orders_for_table(orders_)
        if role == "kitchen":
            orders_ = Order.objects.filter(created_at__date=timezone.now().date(), order_status__in=["processing"]).order_by("created_at")
            data = utils.get_orders_for_kitchen(orders_)
        return Response(data)

    @action(detail=True, methods=["get"], permission_classes=[IsTableUser])
    def get_order(self, request, pk=None):
        order_ = get_object_or_404(Order, pk=pk)
        order_time = order_.paid_at if order_.paid_at else order_.created_at

        if self.request.user.role != "admin" and timezone.now() - order_time > timedelta(hours=3):
            return Response({"detail": "Order is too old"}, status=status.HTTP_403_FORBIDDEN)

        data = utils.get_order_data(order_)
        return Response(data)


class HistoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = History.objects.all()
    # serializer_class = HistorySerializer
    permission_classes = [IsAdminUser | IsManagerUser]

    def get_queryset(self):
        if self.request.user.role == "table":
            return History.objects.filter(user=self.request.user)
        return super().get_queryset()


# Web Views

def user_login(request):
    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data["username"]
            password = form.cleaned_data["password"]
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect("home")
    else:
        form = LoginForm()
    return render(request, "base/login.html", {"form": form})


@login_required
def user_logout(request):
    logout(request)
    return redirect("login")


@login_required
def home(request):
    return render(request, "base/home.html")


@login_required
def custom_meal(request):
    return render(request, "client/custom_meal.html")


@login_required
def custom_add(request, ingredient_id):
    return render(request, "client/custom_add.html", {"ingredient_id": ingredient_id})


@login_required
def cart(request):
    return render(request, "client/cart.html")


@login_required
def orders(request):
    if request.user.role not in ["admin", "manager"]:
        return redirect("home")
    return render(request, "manage/orders.html")


@login_required
@require_POST
def checkout(request):
    try:
        data = json.loads(request.body)
        official_meals = data.get("official_meals", [])
        custom_meals = data.get("custom_Meals", [])

        total_price = utils.big_validator(data)

        nutritional_value = NutritionalValue.objects.create(**data.get("nutritional_value"))
        nutritional_value.save()
        order = Order.objects.create(user=request.user, payment_type=data["payment_type"], raw_price=round(total_price),
                                     nutritional_value=nutritional_value)

        utils.process_official_meal(official_meals, order)
        utils.process_custom_meal(custom_meals, order)
        order.save()

        return JsonResponse({"success": True, "redirect_url": f"/"})
    except ValidationError as e:
        return JsonResponse({"success": False, "error": str(e)}, status=400)
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=400)


@login_required
def product_management(request):
    if request.user.role not in ["admin", "manager"]:
        return redirect("home")
    # Implement product management logic here
    return render(request, "manage/product_management.html")


@login_required
def ingredient_management(request):
    if request.user.role not in ["admin", "manager"]:
        return redirect("home")
    # Implement ingredient management logic here
    return render(request, "manage/ingredient_management.html")


@login_required
def update_order_status(request):
    if request.user.role not in ["admin", "manager"]:
        return JsonResponse({"success": False, "error": "Permission denied"}, status=403)

    order_id = request.POST.get("order_id")
    new_status = request.POST.get("status")
    order = get_object_or_404(Order, id=order_id)
    order.order_status = new_status
    order.save()
    return JsonResponse({"success": True})
