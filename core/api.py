import json
import logging

from django.db import transaction
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django_ratelimit.decorators import ratelimit
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Ingredient, Product, Order, NutritionalValue, Promo, Setting, OrderHistory
from core.utils import utils_api
from core.utils import utils
from .serializers import OrderSerializer, OrderHistorySerializer

logger = logging.getLogger(__name__)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@utils.handle_errors
@ratelimit(key="user", rate="30/m", method=["GET"])
def get_all_products(request):
    products = Product.objects.filter(is_menu=True)
    if products:
        return Response({"products": utils_api.get_all_products(products)}, status=status.HTTP_200_OK)
    return Response({"products": [], "messages": [{"level": "info", "message": "No products found."}]}, status=status.HTTP_404_NOT_FOUND)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@utils.role_redirect(roles=["owner", "administrator", "manager"], redirect_url="home", do_redirect=False)
@utils.handle_errors
@ratelimit(key="user", rate="30/m", method=["GET"])
def get_all_products_control(request):
    if request.user.role == "owner" or request.user.role == "administrator":
        products = Product.objects.all()
    else:
        products = Product.objects.filter(is_menu=True)

    if products:
        filtered_products = utils_api.filter_products(request, products)
        products = [utils_api.get_products_data(product) for product in filtered_products]
        return Response({"products": products}, status=status.HTTP_200_OK)
    return Response({"products": [], "messages": [{"level": "info", "message": "No products found."}]}, status=status.HTTP_404_NOT_FOUND)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@utils.role_redirect(roles=["owner", "administrator", "manager"], redirect_url="home", do_redirect=False)
@utils.handle_errors
@ratelimit(key="user", rate="30/m", method=["GET"])
def get_product_control(request, pk=None):
    product = Product.objects.filter(pk=pk).first()
    if product:
        if request.user.role == "owner" or request.user.role == "administrator":
            return Response({"product": utils_api.get_products_data(product, is_full=True, is_admin=True)}, status=status.HTTP_200_OK)
        else:
            return Response({"product": utils_api.get_products_data(product, is_full=True)}, status=status.HTTP_200_OK)

    return Response({"product": "", "messages": [
        {"level": "error", "message": f"Product #{pk} not found"}]}, status=status.HTTP_404_NOT_FOUND)


@api_view(["PUT"])
@permission_classes([IsAuthenticated])
@utils.role_redirect(roles=["owner", "administrator", "manager"], redirect_url="home", do_redirect=False)
@utils.handle_errors
@ratelimit(key="user", rate="30/m", method=["GET"])
def update_product_control(request, pk=None):
    product = Product.objects.filter(pk=pk).first()
    if product:
        product.is_enabled = not product.is_enabled
        product.save()  # it's important to do .save() bc there's logic to change self availability, depends on enable status & ingredients
        return Response({"product": utils_api.get_products_data(product, is_full=True)}, status=status.HTTP_200_OK)
    return Response({"product": "", "messages": [
        {"level": "error", "message": f"Product #{pk} not found"}]}, status=status.HTTP_404_NOT_FOUND)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@utils.handle_errors
@ratelimit(key="user", rate="30/m", method=["GET"])
def get_ingredients(request):
    """
    Uses for Customers to choose from ingredients for custom meal
    :return: All ingredients that are in the menu.
    """
    ingredients = Ingredient.objects.filter(is_menu=True).select_related("nutritional_value")
    if ingredients:
        ingredients = [utils_api.get_ingredient_data(ingredient) for ingredient in ingredients]
        return Response({"ingredients": ingredients}, status=status.HTTP_200_OK)
    return Response({"ingredients": [], "messages": [
        {"level": "info", "message": "No ingredients found."}]}, status=status.HTTP_404_NOT_FOUND)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@utils.handle_errors
@ratelimit(key="user", rate="30/m", method=["GET"])
def get_ingredient(request, pk=None):
    """
    Uses for Customers to build custom meal
    :return: Ingredient data by PK if it's menu.
    """
    try:
        ingredient = Ingredient.objects.get(pk=pk, is_menu=True)
    except Ingredient.DoesNotExist:
        return Response({"messages": [{"level": "error", "message": "Not Found"}]}, status=status.HTTP_404_NOT_FOUND)
    return Response({"ingredient": utils_api.get_ingredient_data(ingredient)}, status=status.HTTP_200_OK)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@utils.role_redirect(roles=["owner", "administrator", "manager", "kitchen"], redirect_url="home", do_redirect=False)
@utils.handle_errors
@ratelimit(key="user", rate="30/m", method=["GET"])
def get_ingredient_control(request, pk=None):
    """
    Uses in Control Panel to manage ingredients.
    If Admin - ingredient with full info
    If not - ingredient if it's menu and basic info (name, type, img, is_available)
    :param request:
    :param pk:
    :return:
    """
    try:
        if request.user.role == "owner" or request.user.role == "administrator":
            ingredient = Ingredient.objects.get(pk=pk)
            ingredient_data = utils_api.get_ingredient_data_full(ingredient)
        else:
            ingredient = Ingredient.objects.get(pk=pk, is_menu=True)
            ingredient_data = utils_api.get_ingredient_data_lite(ingredient)
    except Ingredient.DoesNotExist:
        return Response({"messages": [{"level": "error", "message": "Not Found"}]}, status=status.HTTP_404_NOT_FOUND)

    return Response({"ingredient": ingredient_data}, status=status.HTTP_200_OK)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@utils.role_redirect(roles=["owner", "administrator", "manager", "kitchen"], redirect_url="home", do_redirect=False)
@utils.handle_errors
@ratelimit(key="user", rate="30/m", method=["GET"])
def get_ingredients_control(request):
    """
    Uses in Control Panel to manage ingredients.
    If Admin - all ingredients, basic info + is_menu + selling price
    If not - only meny ingredients, basic info
    :param request:
    :return:
    """
    if request.user.role == "owner" or request.user.role == "administrator":
        ingredients = Ingredient.objects.all()
        ingredients = [utils_api.get_ingredient_data_lite(ingredient, admin=True) for ingredient in ingredients]
    else:
        ingredients = Ingredient.objects.filter(is_menu=True)
        ingredients = [utils_api.get_ingredient_data_lite(ingredient) for ingredient in ingredients]

    if ingredients:
        return Response({"ingredients": ingredients}, status=status.HTTP_200_OK)
    return Response({"ingredients": [], "messages": [
        {"level": "info", "message": "No ingredients found."}]}, status=status.HTTP_404_NOT_FOUND)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@utils.role_redirect(roles=["owner", "manager", "administrator"], redirect_url="home", do_redirect=False)
@utils.handle_errors
@ratelimit(key="user", rate="30/m", method=["GET"])
def get_order_control(request, pk):
    order = Order.objects.filter(pk=pk).first()
    if order:
        return Response({"order": utils_api.get_order_full(order)}, status=status.HTTP_200_OK)
    return Response({"order": "", "messages": [
        {"level": "error", "message": f"Order #{pk} not found"}
    ]}, status=status.HTTP_404_NOT_FOUND)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@utils.role_redirect(roles=["owner", "manager", "administrator", "kitchen"], redirect_url="home", do_redirect=False)
@utils.handle_errors
@ratelimit(key="user", rate="30/m", method=["GET"])
def get_orders_control(request):
    if request.META.get("HTTP_REFERER").endswith("kitchen/orders/"):
        orders = Order.objects.filter(order_status__in=["cooking"]).order_by("paid_at")
        if orders:
            return Response({"orders": utils_api.get_orders_for_kitchen(orders)}, status=status.HTTP_200_OK)
        return Response({"orders": [], "messages": [{"level": "info", "message": "No orders."}]}, status=status.HTTP_200_OK)

    if request.user.role == "owner" or request.user.role == "administrator":
        orders = Order.objects.all()
    elif request.user.role == "manager":
        orders = Order.objects.filter(created_at__date=timezone.now().date())
    else:
        return Response({"messages": [{"info": "error", "message": "You don't have access to this data."}]}, status.HTTP_403_FORBIDDEN)

    if orders.exists():
        orders = utils_api.filter_orders(request, orders)
        return Response({"orders": utils_api.get_orders_general(orders)})

    return Response({"orders": [], "messages": [{"level": "success", "message": "No orders found."}]}, status=status.HTTP_200_OK)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@utils.role_redirect(roles=["owner"], redirect_url="home", do_redirect=False)
@utils.handle_errors
@ratelimit(key="user", rate="30/m", method=["GET"])
def get_orders_history(request):
    orders = Order.objects.all().order_by('-created_at')
    serializer = OrderSerializer(orders, many=True)
    return Response(serializer.data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@utils.role_redirect(roles=["owner"], redirect_url="home", do_redirect=False)
@utils.handle_errors
@ratelimit(key="user", rate="30/m", method=["GET"])
def get_order_history_detail(request, pk=None):
    history = OrderHistory.objects.filter(order_id=pk).order_by('created_at')
    serializer = OrderHistorySerializer(history, many=True)
    return Response(serializer.data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@utils.handle_errors
@ratelimit(key="user", rate="30/m", method=["GET"])
def get_order_last(request):
    order = Order.objects.filter(user=request.user).order_by("-created_at").first()
    if order and order.show_public:
        order = utils_api.get_order_last(order)
        return Response({"order": order}, status=status.HTTP_200_OK)
    return Response({"order": None, "messages": [
        {"level": "info", "message": "There are no recent orders."}
    ]}, status=status.HTTP_200_OK)


@api_view(["PUT"])
@permission_classes([IsAuthenticated])
@utils.handle_errors
@ratelimit(key="user", rate="30/m", method=["PUT"])
@utils.role_redirect(roles=["owner", "manager", "kitchen", "administrator"], redirect_url="home", do_redirect=False)
def update_order_control(request, pk):
    order = Order.objects.get(pk=pk)

    if not utils_api.can_edit_order(order) and not (request.user.role == "owner" and request.user.is_superuser):
        msg = "This order can no longer be edited as it was placed over a day ago."
        return Response({"messages": [{"level": "warning", "message": msg}]}, status=status.HTTP_400_BAD_REQUEST)

    if request.user.role == "kitchen":
        order.order_status = Order.READY
        order.save()
        return Response({"messages": [{"level": "success", "message": "Ready! Well done!"}]}, status=status.HTTP_200_OK)

    if request.META.get("HTTP_REFERER").endswith("kitchen/orders/"):
        msg = f"{request.user.role.capitalize()} can't update orders from kitchen."
        return Response({"messages": [{"level": "warning", "message": msg}]}, status=status.HTTP_200_OK)

    data = json.loads(request.body)

    order.order_status = data.get("order_status")
    order.order_type = data.get("order_type")
    order.payment_type = data.get("payment_type")
    order.payment_id = data.get("payment_id")
    order.is_paid = data.get("is_paid")
    order.is_refunded = data.get("is_refunded")
    order.private_note = data.get("private_note")
    order.user_last_update = request.user
    order.clean()
    order.save()

    return Response({"messages": [{"level": "success", "message": f"Order #{order.id} updated."}]}, status=status.HTTP_200_OK)


@api_view(["PUT"])
@permission_classes([IsAuthenticated])
@utils.handle_errors
@ratelimit(key="user", rate="30/m", method=["PUT"])
@utils.role_redirect(roles=["owner", "manager", "kitchen", "administrator"], redirect_url="home", do_redirect=False)
def update_ingredient_control(request, pk):
    try:
        ingredient = Ingredient.objects.get(pk=pk)

        if request.user.role != "owner" and request.user.role != "administrator":
            ingredient.is_available = not ingredient.is_available
            ingredient.save()
        else:
            data = json.loads(request.POST.get('data'))
            if 'image' in request.FILES:
                data['image'] = request.FILES['image']

            nutritional_data = data.pop('nutritional_value')
            utils.validate_nutritional_summary(nutritional_data)

            for field, value in nutritional_data.items():
                setattr(ingredient.nutritional_value, field, value)
            ingredient.nutritional_value.save()

            for field, value in data.items():
                setattr(ingredient, field, value)

            ingredient.save()

        return Response({"messages": [{"level": "success", "message": f"{ingredient.name} updated."}]}, status=status.HTTP_200_OK)
    except Ingredient.DoesNotExist:
        return Response({"messages": [{"level": "error", "message": "Not Found"}]}, status=status.HTTP_404_NOT_FOUND)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@utils.handle_errors
@ratelimit(key="user", rate="30/m", method=["POST"])
@utils.role_redirect(roles=["owner", "administrator"], redirect_url="home", do_redirect=False)
def create_ingredient_control(request):
    try:
        data = json.loads(request.POST.get('data'))
        if 'image' in request.FILES:
            data['image'] = request.FILES['image']

        nutritional_value = data.pop('nutritional_value')
        utils.validate_nutritional_summary(nutritional_value)

        nutritional_value = NutritionalValue.objects.create(**nutritional_value)
        id_ = Ingredient.objects.create(**data, nutritional_value=nutritional_value).id

        return Response({"messages": [{"level": "success", "message": f"Ingredient #{id_} created"}]}, status=status.HTTP_200_OK)
    except Ingredient.DoesNotExist:
        return Response({"messages": [{"level": "error", "message": "Not Found"}]}, status=status.HTTP_404_NOT_FOUND)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@utils.handle_errors
@ratelimit(key="user", rate="30/m", method=["GET"])
@utils.role_redirect(roles=["owner", "administrator"], redirect_url="home", do_redirect=False)
def get_promos(request):
    promos = Promo.objects.all()
    promos = [utils_api.get_promo_data(promo) for promo in promos]

    if promos:
        return Response({"promos": promos}, status=status.HTTP_200_OK)
    return Response({"promos": [], "messages": [
        {"level": "info", "message": "No promos found."}]}, status=status.HTTP_404_NOT_FOUND)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@utils.handle_errors
@ratelimit(key="user", rate="30/m", method=["GET"])
@utils.role_redirect(roles=["owner", "administrator"], redirect_url="home", do_redirect=False)
def get_promo(request, pk):
    promo = Promo.objects.filter(pk=pk).first()
    if promo:
        return Response({"promo": utils_api.get_promo_data(promo, full=True)}, status=status.HTTP_200_OK)
    return Response({"promos": [], "messages": [
        {"level": "info", "message": f"Promo #{pk} not found."}]}, status=status.HTTP_404_NOT_FOUND)


@api_view(["PUT"])
@permission_classes([IsAuthenticated])
@utils.handle_errors
@ratelimit(key="user", rate="30/m", method=["PUT"])
@utils.role_redirect(roles=["owner", "administrator"], redirect_url="home", do_redirect=False)
def update_promo(request, pk=None):
    try:
        promo = utils_api.update_promo(Promo.objects.get(pk=pk), request)
    except Promo.DoesNotExist:
        return Response({"messages": [{"level": "error", "message": "Not Found"}]}, status=status.HTTP_404_NOT_FOUND)
    promo.save()

    return Response({"messages": [{"level": "success", "message": f"Promo #{promo.id} updated."}]}, status=status.HTTP_200_OK)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@utils.handle_errors
@ratelimit(key="user", rate="30/m", method=["POST"])
@utils.role_redirect(roles=["owner", "administrator"], redirect_url="home", do_redirect=False)
def create_promo(request):
    promo = utils_api.update_promo(Promo(), request)
    promo.creator = request.user
    promo.save()
    return Response({"messages": [{"level": "success", "message": f"Promo #{promo.id} created."}]}, status=status.HTTP_201_CREATED)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@utils.handle_errors
@ratelimit(key="user", rate="10/m", method=["GET"])
def check_promo(request, promo_code):
    promo = utils.check_promo(promo_code)
    if promo:
        discount = round(promo.discount * 100)
        msg = f"Congratulations! The promo code is active with a max discount of -{discount}%, up to {promo.max_discount:,} IDR."
        return Response({
            "messages": [{"level": "success", "message": msg}],
            "is_active": True,
            "discount": promo.discount,
            "max_discount": promo.max_discount}, status=status.HTTP_200_OK)
    return Response({"messages": [{"level": "warning", "message": "It appears the promo code entered is not valid."}],
                     "is_active": False}, status=status.HTTP_200_OK)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@utils.role_redirect(roles=["kitchen"], redirect_url="home", do_redirect=True)
@utils.handle_errors
@ratelimit(key="user", rate="5/m", method=["POST"])
@ratelimit(key="user", rate="100/h", method=["POST"])
@transaction.atomic
def checkout(request):
    settings = Setting.objects.values().first()
    promo_usage = utils.order_validator(request.data, settings)

    official_meals = request.data.get("official_meals", [])
    custom_meals = request.data.get("custom_meals", [])
    price_base = round(request.data.get("base_price"))
    price_final = round(request.data.get("final_price"))

    # Save nutrition info with 1 number after the decimal point
    nutritional_value = NutritionalValue.objects.create(**{k: round(v, 1) for k, v in request.data["nutritional_value"].items()})
    order = Order.objects.create(user=request.user, user_last_update=request.user, payment_type=request.data["payment_type"],
                                 base_price=price_base, total_price=price_final, nutritional_value=nutritional_value,
                                 tax=settings.get("tax"), service=settings.get("service"))

    if promo_usage:
        promo_usage.user = request.user
        promo_usage.order = order
        promo_usage.save()

        order.promo_usage = promo_usage
        order.save(update_fields=["promo_usage"])

    if official_meals:
        utils.process_official_meal(official_meals, order)
    if custom_meals:
        utils.process_custom_meal(custom_meals, order)

    return Response({"messages": [{"level": "success", "message": f"Order {order.id} has been created. Redirecting..."}],
                     "redirect_url": f"/last-order/"}, status=status.HTTP_200_OK)
