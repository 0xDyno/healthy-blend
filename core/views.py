# views.py

import json
import logging

from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django_ratelimit.decorators import ratelimit
from rest_framework import status
from .models import Order, NutritionalValue
from .forms import LoginForm
from core.utils import utils

logger = logging.getLogger(__name__)


@utils.handle_rate_limit
@ratelimit(key="ip", rate="50/h", method=["POST"])
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
@utils.role_redirect(roles=["kitchen"], redirect_url="home", do_redirect=True)
@require_POST
@utils.handle_rate_limit
@ratelimit(key="user", rate="5/m", method=["POST"])
@ratelimit(key="user", rate="100/h", method=["POST"])
@transaction.atomic
def checkout(request):
    try:
        data = json.loads(request.body)
        promo_usage = utils.big_validator(data)

        official_meals = data.get("official_meals", [])
        custom_meals = data.get("custom_meals", [])
        price_no_fee = round(data.get("raw_price"))
        price_with_fee = round(data.get("total_price"))

        if promo_usage:
            promo_usage.save()

        # Save nutrition info with 1 number after the decimal point
        nutritional_value = NutritionalValue.objects.create(**{k: round(v, 1) for k, v in data["nutritional_value"].items()})
        order = Order.objects.create(user=request.user, user_last_update=request.user, payment_type=data["payment_type"],
                                     base_price=price_no_fee, total_price=price_with_fee, nutritional_value=nutritional_value)

        if promo_usage:
            promo_usage.user = request.user
            promo_usage.order = order
            promo_usage.save(update_fields=["order"])

        if official_meals:
            utils.process_official_meal(official_meals, order)
        if custom_meals:
            utils.process_custom_meal(custom_meals, order)

        return JsonResponse({"messages": [
            {"level": "success", "message": f"Order {order.id} has been created. Redirecting..."}
        ], "redirect_url": f"/last-order/"}, status=status.HTTP_200_OK)
    except ValidationError as e:
        return JsonResponse({"messages": [{"level": "warning", "message": e.messages}]}, status=status.HTTP_400_BAD_REQUEST)


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
