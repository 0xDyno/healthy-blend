# views.py

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django_ratelimit.decorators import ratelimit
from .forms import LoginForm
from core.utils import utils


@utils.handle_errors
@ratelimit(key="ip", rate="50/h", method=["POST"])
@ratelimit(key="ip", rate="5/m", method=["POST"])
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
@utils.role_redirect(roles=["owner", "manager", "administrator"], redirect_url="home", do_redirect=False)
def orders_control(request):
    return render(request, "manage/orders_control.html")


@login_required
@utils.role_redirect(roles=["owner", "manager", "administrator"], redirect_url="home", do_redirect=False)
def orders_control_all(request):
    return render(request, "manage/orders_all.html")


@login_required
@utils.role_redirect(roles=["owner", "manager", "administrator"], redirect_url="home", do_redirect=False)
def product_control(request):
    return render(request, "manage/products.html")


@login_required
@utils.role_redirect(roles=["owner", "manager", "administrator"], redirect_url="home", do_redirect=False)
def promo_control(request):
    return render(request, "manage/promo.html")


@login_required
@utils.role_redirect(roles=["owner", "manager", "administrator"], redirect_url="home", do_redirect=False)
def ingredient_control(request):
    return render(request, "manage/ingredients.html")


@login_required
@utils.role_redirect(roles=["kitchen", "owner", "administrator"], redirect_url="home", do_redirect=False)
def kitchen_orders(request):
    return render(request, "manage/kitchen_orders.html")


@login_required
@utils.role_redirect(roles=["kitchen", "owner", "administrator"], redirect_url="home", do_redirect=False)
def kitchen_ingredients(request):
    return render(request, "manage/kitchen_ingredients.html")


@login_required
@utils.role_redirect(roles=["owner"], redirect_url="orders_control", do_redirect=False)
def history(request):
    return render(request, "manage/history.html")
