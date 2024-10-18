import json
from audioop import reverse

from django.db.models import Sum, F
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import User, Ingredient, Product, Order, OrderProduct, History, ProductIngredient
from .serializers import UserSerializer, IngredientSerializer, ProductSerializer, OrderSerializer, HistorySerializer
from .forms import LoginForm
import logging


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


# API ViewSets

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdminUser]


class IngredientViewSet(viewsets.ModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = [IsAdminUser | IsManagerUser]


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAdminUser | IsManagerUser]

    @action(detail=False, methods=['post'], permission_classes=[IsTableUser])
    def custom(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    @action(detail=True, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def nutritional_info(self, request, pk=None):
        product = self.get_object()
        nutritional_value = product.nutritional_value
        base_calories = max(float(nutritional_value.calories or 0), 1)
        base_grams = float(product.weight or 100)

        def calculate_for_calories(target_calories):
            factor = target_calories / base_calories
            target_grams = base_grams * factor
            return {
                'calories': int(target_calories),
                'grams': round(target_grams, 1),
                'fats': round(float(nutritional_value.fats or 0) * factor, 1),
                'saturated_fats': round(float(nutritional_value.saturated_fats or 0) * factor, 1),
                'carbohydrates': round(float(nutritional_value.carbohydrates or 0) * factor, 1),
                'sugars': round(float(nutritional_value.sugars or 0) * factor, 1),
                'fiber': round(float(nutritional_value.fiber or 0) * factor, 1),
                'proteins': round(float(nutritional_value.proteins or 0) * factor, 1),
                'price': product.get_price_for_calories(target_calories),
            }

        data = {
            'base': {
                'calories': int(base_calories),
                'grams': round(base_grams, 1),
                'price': float(product.price),
                'selling_price': float(product.get_selling_price()),
                'is_custom_price': product.custom_price is not None,
            },
            'variants': {
                '400': calculate_for_calories(400),
                '600': calculate_for_calories(600),
                '800': calculate_for_calories(800),
            }
        }

        return Response(data)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def add_to_cart(self, request, pk=None):
        product = self.get_object()
        calories = int(request.data.get('calories', 600))
        quantity = int(request.data.get('quantity', 1))

        # Получаем или создаем текущий заказ пользователя
        order, created = Order.objects.get_or_create(
            table=request.user,
            order_status='pending',
            defaults={'price': 0, 'total_price': 0}  # Устанавливаем начальные значения
        )

        # Добавляем продукт в заказ
        order_product, created = OrderProduct.objects.get_or_create(
            order=order,
            product=product,
            defaults={'quantity': 0}
        )
        order_product.quantity = F('quantity') + quantity
        order_product.save()

        # Обновляем общую стоимость заказа
        order.total_price = order.dishes.aggregate(
            total=Sum(F('product__price') * F('quantity'))
        )['total'] or 0
        order.price = order.total_price  # Устанавливаем price равным total_price
        order.save()

        # Рассчитываем суммарную информацию о заказе
        order_summary = self.calculate_order_summary(order)

        return Response({
            'success': True,
            'item_count': order.dishes.count(),
            'total_price': order.total_price,
            'order_summary': order_summary
        })

    def calculate_order_summary(self, order):
        summary = {
            'total_price': 0,
            'total_kcal': 0,
            'total_fat': 0,
            'total_saturated_fat': 0,
            'total_carbs': 0,
            'total_sugar': 0,
            'total_fiber': 0,
            'total_protein': 0,
        }

        for order_product in order.dishes.all():
            product = order_product.product
            quantity = order_product.quantity
            nutritional_value = product.nutritional_value

            summary['total_price'] += product.get_selling_price() * quantity
            summary['total_kcal'] += float(nutritional_value.calories) * quantity
            summary['total_fat'] += float(nutritional_value.fats) * quantity
            summary['total_saturated_fat'] += float(nutritional_value.saturated_fats) * quantity
            summary['total_carbs'] += float(nutritional_value.carbohydrates) * quantity
            summary['total_sugar'] += float(nutritional_value.sugars) * quantity
            summary['total_fiber'] += float(nutritional_value.fiber) * quantity
            summary['total_protein'] += float(nutritional_value.proteins) * quantity

        return summary

    @action(detail=True, methods=['patch'], permission_classes=[permissions.IsAdminUser])
    def update_price(self, request, pk=None):
        product = self.get_object()
        custom_price = request.data.get('custom_price')
        price_multiplier = request.data.get('price_multiplier')

        if custom_price is not None:
            product.custom_price = custom_price
        elif price_multiplier is not None:
            product.price_multiplier = price_multiplier
            product.custom_price = None
        else:
            return Response({'error': 'Either custom_price or price_multiplier must be provided'}, status=400)

        product.save()
        return Response({
            'success': True,
            'selling_price': float(product.get_selling_price()),
            'is_custom_price': product.custom_price is not None,
        })


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer

    def get_permissions(self):
        if self.action in ['create', 'list', 'retrieve']:
            return [IsTableUser()]
        elif self.action in ['update', 'partial_update']:
            return [IsManagerUser()]
        return [IsAdminUser()]

    @action(detail=False, methods=['get'], permission_classes=[IsTableUser])
    def current(self, request):
        order = Order.objects.filter(table=request.user, order_status__in=['pending', 'processing']).first()
        if order:
            serializer = self.get_serializer(order)
            return Response(serializer.data)
        return Response({'detail': 'No current order found.'}, status=status.HTTP_404_NOT_FOUND)


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
    return render(request, 'login.html', {'form': form})


@login_required
def user_logout(request):
    logout(request)
    return redirect('login')


@login_required
def home(request):
    products = Product.objects.filter(is_official=True)
    context = {
        'products': products,
    }
    return render(request, 'home.html', context)


@login_required
def custom_meal(request):
    ingredients = Ingredient.objects.filter(available=True)
    return render(request, 'custom_meal.html', {'ingredients': ingredients})


@login_required
def ingredient_detail(request, ingredient_id):
    ingredient = get_object_or_404(Ingredient, id=ingredient_id)
    return render(request, 'ingredient_detail.html', {'ingredient': ingredient})


@login_required
def get_ingredients(request):
    sort_by = request.GET.get('sort', 'protein')

    sort_mapping = {
        'protein': '-nutritional_value__proteins',
        'fat': '-nutritional_value__fats',
        'fiber': '-nutritional_value__fiber',
        'carbs': '-nutritional_value__carbohydrates',
        'sugar': '-nutritional_value__sugars',
    }

    ingredients = Ingredient.objects.filter(available=True).order_by(sort_mapping.get(sort_by, 'name'))

    data = [{
        'id': ingredient.id,
        'name': ingredient.name,
        'description': ingredient.description,
        'price_per_gram': ingredient.price_per_gram,
    } for ingredient in ingredients]

    return JsonResponse(data, safe=False)


@login_required
def get_custom_meal_summary(request):
    custom_meal, created = Product.objects.get_or_create(
        name=f"Custom Meal - {request.user.username}",
        is_official=False,
        defaults={'description': 'Custom meal created by user'}
    )

    if created or not custom_meal.productingredient_set.exists():
        return JsonResponse({
            'total_price': 0,
            'total_kcal': 0,
            'total_fat': 0,
            'total_saturated_fat': 0,
            'total_carbs': 0,
            'total_sugar': 0,
            'total_fiber': 0,
            'total_protein': 0,
            'ingredients': [],
        })

    nutritional_value = custom_meal.nutritional_value

    ingredients = [
        {
            'name': pi.ingredient.name,
            'weight': pi.weight_grams
        }
        for pi in custom_meal.productingredient_set.all()
    ]

    return JsonResponse({
        'total_price': custom_meal.get_selling_price(),
        'total_kcal': float(nutritional_value.calories),
        'total_fat': float(nutritional_value.fats),
        'total_saturated_fat': float(nutritional_value.saturated_fats),
        'total_carbs': float(nutritional_value.carbohydrates),
        'total_sugar': float(nutritional_value.sugars),
        'total_fiber': float(nutritional_value.fiber),
        'total_protein': float(nutritional_value.proteins),
        'ingredients': ingredients,
    })


@login_required
@require_POST
def add_ingredient_to_custom_meal(request):
    data = json.loads(request.body)
    ingredient_id = data.get('ingredient_id')
    amount = int(data.get('amount'))

    ingredient = get_object_or_404(Ingredient, id=ingredient_id)

    custom_meal, created = Product.objects.get_or_create(
        name=f"Custom Meal - {request.user.username}",
        is_official=False,
        defaults={'description': 'Custom meal created by user'}
    )

    existing_ingredient = custom_meal.productingredient_set.filter(ingredient=ingredient).first()

    if existing_ingredient:
        existing_ingredient.weight_grams += amount
        existing_ingredient.save()
    else:
        ProductIngredient.objects.create(
            product=custom_meal,
            ingredient=ingredient,
            weight_grams=amount
        )

    custom_meal.save()

    return JsonResponse({'success': True})


@login_required
@require_POST
def remove_ingredient_from_custom_meal(request):
    logger.info("Starting remove_ingredient_from_custom_meal")
    data = json.loads(request.body)
    ingredient_id = data.get('ingredient_id')

    logger.info(f"Attempting to remove ingredient: {ingredient_id}")

    custom_meal = Product.objects.filter(
        name=f"Custom Meal - {request.user.username}",
        is_official=False
    ).first()

    if custom_meal:
        logger.info(f"Custom meal found: {custom_meal.id}")
        deleted, _ = ProductIngredient.objects.filter(product=custom_meal, ingredient_id=ingredient_id).delete()
        logger.info(f"Deleted {deleted} ProductIngredient(s)")
        custom_meal.save()  # This will trigger recalculation of nutritional values
        logger.info("Custom meal saved")
    else:
        logger.error("Custom meal not found")

    return JsonResponse({'success': True})


@login_required
@require_POST
def add_custom_meal_to_order(request):
    logger.info("Starting add_custom_meal_to_order")
    custom_meal = Product.objects.filter(
        name=f"Custom Meal - {request.user.username}",
        is_official=False
    ).first()

    if not custom_meal or not custom_meal.productingredient_set.exists():
        logger.error("No custom meal found or it is empty")
        return JsonResponse({'success': False, 'error': 'No custom meal found or it is empty'})

    logger.info(f"Custom meal found: {custom_meal.id}")

    # Create a new order or get the current pending order
    order, created = Order.objects.get_or_create(
        table=request.user,
        order_status='pending',
        defaults={'price': 0, 'total_price': 0}
    )

    logger.info(f"Order {'created' if created else 'found'}: {order.id}")

    # Create a new Product for the custom meal
    new_product = Product.objects.create(
        name=f"Custom Meal - {request.user.username}",
        description="Custom meal created by user",
        is_official=False,
        price=custom_meal.price,
    )

    logger.info(f"New product created: {new_product.id}")

    # Copy ingredients from custom meal to new product
    for pi in custom_meal.productingredient_set.all():
        ProductIngredient.objects.create(
            product=new_product,
            ingredient=pi.ingredient,
            weight_grams=pi.weight_grams
        )

    logger.info("Ingredients copied to new product")

    # Add the new product to the order
    order_product = OrderProduct.objects.create(
        order=order,
        product=new_product,
        quantity=1
    )

    logger.info(f"OrderProduct created: {order_product.id}")

    # Update order total price
    order.total_price = order.dishes.aggregate(
        total=Sum(F('product__price') * F('quantity'))
    )['total'] or 0
    order.price = order.total_price
    order.save()

    logger.info(f"Order updated. New total price: {order.total_price}")

    # Clear the custom meal
    custom_meal.delete()

    logger.info("Custom meal deleted")

    return JsonResponse({'success': True})


@login_required
def menu(request):
    products = Product.objects.all()
    return render(request, 'menu.html', {'products': products})


@login_required
def user_management(request):
    if request.user.role != 'admin':
        return redirect('home')
    # Implement user management logic here
    return render(request, 'user_management.html')


@login_required
def product_management(request):
    if request.user.role not in ['admin', 'manager']:
        return redirect('home')
    # Implement product management logic here
    return render(request, 'product_management.html')


@login_required
def ingredient_management(request):
    if request.user.role not in ['admin', 'manager']:
        return redirect('home')
    # Implement ingredient management logic here
    return render(request, 'ingredient_management.html')


@login_required
def cart(request):
    # В будущем здесь будет логика получения корзины пользователя
    cart_items = []
    total_price = 0
    return render(request, 'cart.html', {'cart_items': cart_items, 'total_price': total_price})


@login_required
def orders(request):
    if request.user.role not in ['admin', 'manager']:
        return redirect('home')
    orders = Order.objects.all().order_by('-created_at')
    return render(request, 'orders.html', {'orders': orders})


@login_required
@require_POST
def add_to_cart(request):
    product_id = request.POST.get('product_id')
    # Здесь будет логика добавления товара в корзину
    return JsonResponse({'success': True})


@login_required
@require_POST
def remove_from_cart(request):
    product_id = request.POST.get('product_id')
    # Здесь будет логика удаления товара из корзины
    return JsonResponse({'success': True})


@login_required
def checkout(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        cart_data = data.get('cart', [])
        payment_type = data.get('payment_type')

        if not cart_data:
            return JsonResponse({'success': False, 'error': 'Cart is empty'})

        if not payment_type:
            return JsonResponse({'success': False, 'error': 'Payment type is required'})

        total_price = sum(item['price'] * item['quantity'] for item in cart_data)

        order = Order.objects.create(
            table=request.user,
            price=total_price,
            total_price=total_price,
            order_status='pending',
            payment_type=payment_type
        )

        for item in cart_data:
            product = get_object_or_404(Product, id=item['productId'])
            OrderProduct.objects.create(
                order=order,
                product=product,
                quantity=item['quantity']
            )

        return JsonResponse({'success': True, 'redirect_url': reverse('order_confirmation', args=[order.id])})

    return render(request, 'checkout.html')


@login_required
def order_confirmation(request, order_id):
    order = get_object_or_404(Order, id=order_id, table=request.user)
    return render(request, 'order_confirmation.html', {'order': order})


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
