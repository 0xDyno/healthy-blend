# views.py

import json
import logging

from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Ingredient, Product, Order, NutritionalValue
from .forms import LoginForm
from core.utils import utils_api
from core.utils import utils

logger = logging.getLogger(__name__)


# ------------------------ API ------------------------------------------------------------------------------------------------

@api_view(["GET"])
@login_required
def api_get_ingredient(request, pk=None):
    ingredient = get_object_or_404(Ingredient, pk=pk)
    data = utils_api.get_ingredient_data(ingredient)

    return Response(data)


@api_view(["GET"])
@login_required
def api_get_all_ingredients(request):
    ingredients = Ingredient.objects.filter()
    data = [utils_api.get_ingredient_data(ingredient) for ingredient in ingredients]
    return Response(data)


@api_view(["GET"])
@login_required
def api_get_all_products(request):
    products = Product.objects.filter(is_menu=True)
    data = utils_api.get_all_products(products)
    return Response(data)


@api_view(["GET"])
@login_required
def api_get_order(request, pk):
    utils.verify_if_manager(request.user)
    order = utils_api.get_order_full(Order.objects.get(pk=pk))
    return Response(order)


@csrf_exempt
@api_view(["GET"])
@login_required
def api_get_orders(request):
    now = timezone.now()
    data = Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)
    if request.user.role == "admin":
        orders = Order.objects.all().order_by("-created_at")
        data = utils_api.get_orders_general(orders)
    if request.user.role == "manager":
        orders = Order.objects.filter(created_at__date=now.date()).order_by("-created_at")
        data = utils_api.get_orders_general(orders)
    if request.user.role == "table":
        order = Order.objects.filter(user=request.user).order_by("-created_at").first()
        data = [utils_api.get_order_for_table(order)]
    if request.user.role == "kitchen":
        orders = Order.objects.filter(created_at__date=timezone.now().date(), order_status__in=["cooking"]).order_by("created_at")
        data = utils_api.get_orders_for_kitchen(orders)
    return Response(data)


@api_view(["PUT"])
@login_required
def api_update_order(request, pk):
    utils.verify_if_manager(request.user)
    data = json.loads(request.body)

    order = Order.objects.get(pk=pk)
    order.order_status = data.get("order_status")
    order.order_type = data.get("order_type")
    order.payment_type = data.get("payment_type")
    order.payment_id = data.get("payment_id")
    order.is_paid = data.get("is_paid")
    order.is_refunded = data.get("is_refunded")
    order.private_note = data.get("private_note")
    try:
        order.clean()
    except ValidationError as e:
        return JsonResponse({"detail": e.messages}, status=status.HTTP_400_BAD_REQUEST)
    order.save()

    return JsonResponse({'message': 'Order updated successfully'}, status=status.HTTP_200_OK)


# ------------------------ WEB views ------------------------------------------------------------------------------------------------

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
def last_order(request):
    if request.user.role != "table":
        return redirect("home")
    return render(request, "client/order.html")


@login_required
def order_management(request):
    if request.user.role != "admin" and request.user.role != "manager":
        return redirect("home")
    return render(request, "manage/order_management.html")


@login_required
@require_POST
def checkout(request):
    try:
        data = json.loads(request.body)
        official_meals = data.get("official_meals", [])
        custom_meals = data.get("custom_meals", [])

        utils.big_validator(data)
        price_no_fee = round(data.get("raw_price"))
        price_with_fee = round(data.get("total_price"))

        nutritional_value = NutritionalValue.objects.create(**data.get("nutritional_value"))
        nutritional_value.save()
        order = Order.objects.create(user=request.user, user_last_update=request.user, payment_type=data["payment_type"],
                                     base_price=price_no_fee, total_price=price_with_fee, nutritional_value=nutritional_value)

        utils.process_official_meal(official_meals, order)
        utils.process_custom_meal(custom_meals, order)
        order.save()

        return JsonResponse({"success": True, "redirect_url": f"/last-order/"})
    except ValidationError as e:
        return JsonResponse({"success": False, "error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


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
        return JsonResponse({"success": False, "error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)

    order_id = request.POST.get("order_id")
    new_status = request.POST.get("status")
    order = get_object_or_404(Order, id=order_id)
    order.order_status = new_status
    order.user_last_update = request.user
    order.save()
    return JsonResponse({"success": True}, status.HTTP_200_OK)
