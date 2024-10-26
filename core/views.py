# views.py

import json
import logging

from django.contrib import messages
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
    ingredients = Ingredient.objects.all()
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
@utils.role_redirect(roles=["admin", "manager"], redirect_url="home", do_redirect=False)
def api_get_order(request, pk):
    order = utils_api.get_order_full(Order.objects.get(pk=pk))
    return Response(order)


@api_view(["GET"])
@login_required
@utils.role_redirect(roles=["table"], redirect_url="home", do_redirect=False)
def api_get_order_table(request):
    order = Order.objects.filter(user=request.user).order_by("-created_at").first()
    return Response([utils_api.get_order_for_table(order)])


@api_view(["GET"])
@login_required
@utils.role_redirect(roles=["admin", "kitchen", "manager"], redirect_url="home", do_redirect=False)
def api_get_orders_kitchen(request):
    orders = Order.objects.filter(order_status__in=["cooking"]).order_by("paid_at")
    return Response(utils_api.get_orders_for_kitchen(orders))


@api_view(["GET"])
@login_required
@utils.role_redirect(roles=["admin", "manager"], redirect_url="home", do_redirect=False)
def api_get_orders(request):
    if request.user.role == "admin":
        orders = Order.objects.all()
    if request.user.role == "manager":
        orders = Order.objects.filter(created_at__date=timezone.now().date())

    try:
        orders = utils_api.filter_orders(request, orders)
        return Response(utils_api.get_orders_general(orders))
    except Exception as e:
        msg = f"Error api/get/orders. Please make a photo and send to the admin. Info:\n{e.__str__()}"
        return Response({"details": msg}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["PUT"])
@login_required
@utils.role_redirect(roles=["admin", "manager", "kitchen"], redirect_url="home", do_redirect=False)
def api_update_order(request, pk):
    order = Order.objects.get(pk=pk)

    if request.user.role == "kitchen":
        order.order_status = Order.READY
        order.save()
        return JsonResponse({}, status=status.HTTP_200_OK)

    if request.META.get("HTTP_REFERER").endswith("kitchen/"):
        print(f"User ({request.user.role}, id {request.user.id}) tried to update Order from {request.META.get('HTTP_REFERER')}")
        return JsonResponse({"detail": "You can't do it from here"}, status=status.HTTP_403_FORBIDDEN)

    data = json.loads(request.body)

    order.order_status = data.get("order_status")
    order.order_type = data.get("order_type")
    order.payment_type = data.get("payment_type")
    order.payment_id = data.get("payment_id")
    order.is_paid = data.get("is_paid")
    order.is_refunded = data.get("is_refunded")
    order.private_note = data.get("private_note")
    order.user_last_update = request.user
    try:
        order.clean()
    except ValidationError as e:
        return JsonResponse({"detail": e.messages}, status=status.HTTP_400_BAD_REQUEST)
    order.save()

    return JsonResponse({'message': 'Order updated successfully'}, status=status.HTTP_200_OK)


@api_view(["PUT"])
@login_required
@utils.role_redirect(roles=["admin", "manager", "kitchen"], redirect_url="home", do_redirect=False)
def api_update_ingredient(request, pk):
    try:
        ingredient = Ingredient.objects.get(pk=pk)
    except Ingredient.DoesNotExist:
        return JsonResponse({"detail": "Not Found"}, status=status.HTTP_404_NOT_FOUND)

    ingredient.is_available = not ingredient.is_available
    ingredient.save()

    return JsonResponse({}, status=status.HTTP_200_OK)


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
@utils.role_redirect(roles=["table"], redirect_url="home", do_redirect=True)
def user_logout(request):
    logout(request)
    return redirect("login")


@login_required
@utils.role_redirect(roles=["kitchen"], redirect_url="kitchen", do_redirect=True)
def home(request):
    return render(request, "client/home.html")


@login_required
@utils.role_redirect(roles=["kitchen"], redirect_url="home", do_redirect=True)
def custom_meal(request):
    return render(request, "client/custom_meal.html")


@login_required
@utils.role_redirect(roles=["kitchen"], redirect_url="home", do_redirect=True)
def custom_add(request, ingredient_id):
    return render(request, "client/custom_add.html", {"ingredient_id": ingredient_id})


@login_required
@utils.role_redirect(roles=["kitchen"], redirect_url="home", do_redirect=True)
def cart(request):
    return render(request, "client/cart.html")


@login_required
@utils.role_redirect(roles=["table"], redirect_url="home", do_redirect=False)
def last_order(request):
    return render(request, "client/order.html")


@login_required
@require_POST
@utils.role_redirect(roles=["kitchen"], redirect_url="home", do_redirect=True)
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


@login_required
@utils.role_redirect(roles=["admin", "manager"], redirect_url="home", do_redirect=False)
def orders_control(request):
    return render(request, "manage/orders_control.html")


@login_required
@utils.role_redirect(roles=["admin", "manager"], redirect_url="home", do_redirect=False)
def orders_all(request):
    return render(request, "manage/orders_all.html")


@login_required
@utils.role_redirect(roles=["admin", "manager"], redirect_url="home", do_redirect=False)
def product_management(request):
    return render(request, "manage/products.html")


@login_required
@utils.role_redirect(roles=["admin", "manager"], redirect_url="home", do_redirect=False)
def ingredient_management(request):
    return render(request, "manage/ingredients.html")


@login_required
@utils.role_redirect(roles=["kitchen", "admin"], redirect_url="home", do_redirect=False)
def kitchen(request):
    return render(request, "manage/kitchen.html")