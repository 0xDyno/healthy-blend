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
@utils.role_redirect(roles=["owner", "manager", "administrator"], redirect_url="home", do_redirect=False)
def api_get_order(request, pk):
    order = Order.objects.filter(pk=pk).first()
    if order:
        return JsonResponse({"order": utils_api.get_order_full(order)}, status=status.HTTP_200_OK)
    return JsonResponse({"order": "", "messages": [
        {"level": "error", "message": f"Order #{pk} not found"}
    ]}, status=status.HTTP_404_NOT_FOUND)


@api_view(["GET"])
@login_required
@utils.role_redirect(roles=["owner", "manager", "administrator"], redirect_url="home", do_redirect=False)
def api_get_orders(request):
    if request.user.role == "owner" or request.user.role == "administrator":
        orders = Order.objects.all()
    elif request.user.role == "manager":
        orders = Order.objects.filter(created_at__date=timezone.now().date())
    else:
        return JsonResponse({"messages": [{"info": "error", "message": "You don't have access to this data."}]}, status.HTTP_403_FORBIDDEN)

    if orders.exists():
        try:
            orders = utils_api.filter_orders(request, orders)
        except Exception as e:
            msg = f"Error api/get/orders w/ filtering. Please make a photo and send to the tech team. Info:\n{e.__str__()}"
            return JsonResponse({"orders": [], "messages": [{"level": "error", "message": msg}]})

    if orders:
        return JsonResponse({"orders": utils_api.get_orders_general(orders)})
    return JsonResponse({"orders": [], "messages": [{"level": "success", "message": "No orders found."}]}, status=status.HTTP_200_OK)


@api_view(["GET"])
@login_required
def api_get_order_last(request):
    order = Order.objects.filter(user=request.user).order_by("-created_at").first()
    if order and order.show_public:
        order = utils_api.get_order_last(order)
        return JsonResponse({"order": order}, status=status.HTTP_200_OK)
    return JsonResponse({"order": None, "messages": [
        {"level": "info", "message": "There are no recent orders."}
    ]}, status=status.HTTP_200_OK)


@api_view(["GET"])
@login_required
@utils.role_redirect(roles=["owner", "kitchen", "manager", "administrator"], redirect_url="home", do_redirect=False)
def api_get_orders_kitchen(request):
    orders = Order.objects.filter(order_status__in=["cooking"]).order_by("paid_at")
    if orders:
        return Response({"orders": utils_api.get_orders_for_kitchen(orders)}, status=status.HTTP_200_OK)
    return JsonResponse({"orders": [], "messages": [{"level": "info", "message": "No orders."}]}, status=status.HTTP_200_OK)


@api_view(["PUT"])
@login_required
@utils.role_redirect(roles=["owner", "manager", "kitchen", "administrator"], redirect_url="home", do_redirect=False)
def api_update_order(request, pk):
    order = Order.objects.get(pk=pk)

    if not utils_api.can_edit_order(order) and not (request.user.role == "owner" and request.user.is_superuser):
        msg = "This order can no longer be edited as it was placed over a day ago."
        return JsonResponse({"messages": [{"level": "warning", "message": msg}]}, status=status.HTTP_400_BAD_REQUEST)

    if request.user.role == "kitchen":
        order.order_status = Order.READY
        order.save()
        return JsonResponse({"messages": [{"level": "success", "message": "Ready! Well done!"}]}, status=status.HTTP_200_OK)

    if request.META.get("HTTP_REFERER").endswith("kitchen/"):
        msg = f"{request.user.role.capitalize()} can't update orders from kitchen."
        return JsonResponse({"messages": [{"level": "warning", "message": msg}]}, status=status.HTTP_200_OK)

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
        return JsonResponse({"messages": [{"level": "warning", "message": e.messages}]}, status=status.HTTP_400_BAD_REQUEST)
    order.save()

    return JsonResponse({"messages": [{"level": "success", "message": f"Order #{order.id} updated."}]}, status=status.HTTP_200_OK)


@api_view(["PUT"])
@login_required
@utils.role_redirect(roles=["owner", "manager", "kitchen", "administrator"], redirect_url="home", do_redirect=False)
def api_update_ingredient(request, pk):
    try:
        ingredient = Ingredient.objects.get(pk=pk)
    except Ingredient.DoesNotExist:
        return JsonResponse({"messages": [{"level": "error", "message": "Not Found"}]}, status=status.HTTP_200_OK)

    ingredient.is_available = not ingredient.is_available
    ingredient.save()

    return JsonResponse({"messages": [{"level": "success", "message": f"{ingredient.name} updated."}]}, status=status.HTTP_200_OK)


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
    return render(request, "client/login.html", {"form": form})


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
        order = Order.objects.create(user=request.user, user_last_update=request.user, payment_type=data["payment_type"],
                                     base_price=price_no_fee, total_price=price_with_fee, nutritional_value=nutritional_value)

        utils.process_official_meal(official_meals, order)
        utils.process_custom_meal(custom_meals, order)
        order.save()

        return JsonResponse({"messages": [
            {"level": "success", "message": f"Order {order.id} has been created"}
        ], "redirect_url": f"/last-order/"}, status=status.HTTP_200_OK)
    except ValidationError as e:
        return JsonResponse({"messages": [{"level": "warning", "message": e.messages}]}, status=status.HTTP_200_OK)


@login_required
@utils.role_redirect(roles=["owner", "manager", "administrator"], redirect_url="home", do_redirect=False)
def orders_control(request):
    return render(request, "manage/orders_control.html")


@login_required
@utils.role_redirect(roles=["owner", "manager", "administrator"], redirect_url="home", do_redirect=False)
def orders_all(request):
    return render(request, "manage/orders_all.html")


@login_required
@utils.role_redirect(roles=["owner", "manager", "administrator"], redirect_url="home", do_redirect=False)
def product_management(request):
    return render(request, "manage/products.html")


@login_required
@utils.role_redirect(roles=["owner", "manager", "administrator"], redirect_url="home", do_redirect=False)
def ingredient_management(request):
    return render(request, "manage/ingredients.html")


@login_required
@utils.role_redirect(roles=["kitchen", "owner", "administrator"], redirect_url="home", do_redirect=False)
def kitchen_orders(request):
    return render(request, "manage/kitchen_orders.html")


@login_required
@utils.role_redirect(roles=["kitchen", "owner", "administrator"], redirect_url="home", do_redirect=False)
def kitchen_ingredients(request):
    return render(request, "manage/kitchen_ingredients.html")
