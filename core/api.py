import json

from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.utils import timezone
from django_ratelimit.decorators import ratelimit
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

from .models import Ingredient, Product, Order, NutritionalValue
from core.utils import utils_api
from core.utils import utils


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@utils.handle_rate_limit
@ratelimit(key="user", rate="30/m", method=["GET"])
def get_all_products(request):
    products = Product.objects.filter(is_menu=True)
    if products:
        return JsonResponse({"products": utils_api.get_all_products(products)}, status=status.HTTP_200_OK)
    return JsonResponse({"products": [], "messages": [{"level": "info", "message": "No products found."}]}, status=status.HTTP_404_NOT_FOUND)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@utils.handle_rate_limit
@ratelimit(key="user", rate="30/m", method=["GET"])
def get_all_products_control(request):
    pass


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@utils.handle_rate_limit
@ratelimit(key="user", rate="30/m", method=["GET"])
def get_ingredients(request):
    """
    Uses for Customers to choose from ingredients for custom meal
    :return: All ingredients that are in the menu.
    """
    ingredients = Ingredient.objects.filter(is_menu=True).select_related("nutritional_value")
    if ingredients:
        ingredients = [utils_api.get_ingredient_data(ingredient) for ingredient in ingredients]
        return JsonResponse({"ingredients": ingredients}, status=status.HTTP_200_OK)
    return JsonResponse({"ingredients": [], "messages": [
        {"level": "info", "message": "No ingredients found."}]}, status=status.HTTP_404_NOT_FOUND)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@utils.handle_rate_limit
@ratelimit(key="user", rate="30/m", method=["GET"])
def get_ingredient(request, pk=None):
    """
    Uses for Customers to build custom meal
    :return: Ingredient data by PK if it's menu.
    """
    try:
        ingredient = Ingredient.objects.get(pk=pk, is_menu=True)
    except Ingredient.DoesNotExist:
        return JsonResponse({"messages": [{"level": "error", "message": "Not Found"}]}, status=status.HTTP_404_NOT_FOUND)
    return JsonResponse({"ingredient": utils_api.get_ingredient_data(ingredient)}, status=status.HTTP_200_OK)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@utils.role_redirect(roles=["owner", "administrator", "manager", "kitchen"], redirect_url="home", do_redirect=False)
@utils.handle_rate_limit
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
        return JsonResponse({"messages": [{"level": "error", "message": "Not Found"}]}, status=status.HTTP_404_NOT_FOUND)

    return JsonResponse({"ingredient": ingredient_data}, status=status.HTTP_200_OK)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@utils.role_redirect(roles=["owner", "administrator", "manager", "kitchen"], redirect_url="home", do_redirect=False)
@utils.handle_rate_limit
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
        return JsonResponse({"ingredients": ingredients}, status=status.HTTP_200_OK)
    return JsonResponse({"ingredients": [], "messages": [
        {"level": "info", "message": "No ingredients found."}]}, status=status.HTTP_404_NOT_FOUND)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@utils.role_redirect(roles=["owner", "manager", "administrator"], redirect_url="home", do_redirect=False)
@utils.handle_rate_limit
@ratelimit(key="user", rate="30/m", method=["GET"])
def get_order_control(request, pk):
    order = Order.objects.filter(pk=pk).first()
    if order:
        return JsonResponse({"order": utils_api.get_order_full(order)}, status=status.HTTP_200_OK)
    return JsonResponse({"order": "", "messages": [
        {"level": "error", "message": f"Order #{pk} not found"}
    ]}, status=status.HTTP_404_NOT_FOUND)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@utils.role_redirect(roles=["owner", "manager", "administrator", "kitchen"], redirect_url="home", do_redirect=False)
@utils.handle_rate_limit
@ratelimit(key="user", rate="30/m", method=["GET"])
def get_orders_control(request):
    if request.META.get("HTTP_REFERER").endswith("kitchen/"):
        orders = Order.objects.filter(order_status__in=["cooking"]).order_by("paid_at")
        if orders:
            return JsonResponse({"orders": utils_api.get_orders_for_kitchen(orders)}, status=status.HTTP_200_OK)
        return JsonResponse({"orders": [], "messages": [{"level": "info", "message": "No orders."}]}, status=status.HTTP_200_OK)

    if request.user.role == "owner" or request.user.role == "administrator":
        orders = Order.objects.all()
    elif request.user.role == "manager":
        orders = Order.objects.filter(created_at__date=timezone.now().date())
    else:
        return JsonResponse({"messages": [{"info": "error", "message": "You don't have access to this data."}]}, status.HTTP_403_FORBIDDEN)

    if orders.exists():
        orders = utils_api.filter_orders(request, orders)
        return JsonResponse({"orders": utils_api.get_orders_general(orders)})

    return JsonResponse({"orders": [], "messages": [{"level": "success", "message": "No orders found."}]}, status=status.HTTP_200_OK)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@utils.handle_rate_limit
@ratelimit(key="user", rate="30/m", method=["GET"])
def get_order_last(request):
    order = Order.objects.filter(user=request.user).order_by("-created_at").first()
    if order and order.show_public:
        order = utils_api.get_order_last(order)
        return JsonResponse({"order": order}, status=status.HTTP_200_OK)
    return JsonResponse({"order": None, "messages": [
        {"level": "info", "message": "There are no recent orders."}
    ]}, status=status.HTTP_200_OK)


@api_view(["PUT"])
@permission_classes([IsAuthenticated])
@utils.handle_rate_limit
@ratelimit(key="user", rate="30/m", method=["PUT"])
@utils.role_redirect(roles=["owner", "manager", "kitchen", "administrator"], redirect_url="home", do_redirect=False)
def update_order(request, pk):
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
@permission_classes([IsAuthenticated])
@utils.handle_rate_limit
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

        return JsonResponse({"messages": [{"level": "success", "message": f"{ingredient.name} updated."}]}, status=status.HTTP_200_OK)
    except Ingredient.DoesNotExist:
        return JsonResponse({"messages": [{"level": "error", "message": "Not Found"}]}, status=status.HTTP_404_NOT_FOUND)
    except ValidationError as e:
        return JsonResponse({"messages": [{"level": "warning", "message": e.messages}]}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@utils.handle_rate_limit
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

        return JsonResponse({"messages": [{"level": "success", "message": f"Ingredient #{id_} created"}]}, status=status.HTTP_200_OK)
    except Ingredient.DoesNotExist:
        return JsonResponse({"messages": [{"level": "error", "message": "Not Found"}]}, status=status.HTTP_404_NOT_FOUND)
    except ValidationError as e:
        return JsonResponse({"messages": [{"level": "warning", "message": e.messages}]}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@utils.handle_rate_limit
@ratelimit(key="user", rate="10/m", method=["GET"])
def check_promo(request, promo_code):
    if utils.check_promo(promo_code):
        return JsonResponse({"messages": [{"level": "success", "message": "Good to go! The promo code is active."}],
                             "is_active": True}, status=status.HTTP_200_OK)
    return JsonResponse({"messages": [{"level": "info", "message": "It appears the promo code entered is not valid.",
                                       "is_active": False}]}, status=status.HTTP_204_NO_CONTENT)
