from django.db.models import Sum, F
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import User, Ingredient, Product, Order, OrderProduct, History
from .serializers import UserSerializer, IngredientSerializer, ProductSerializer, OrderSerializer, HistorySerializer
from .forms import LoginForm


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
    # Implement custom meal creation logic here
    return render(request, 'custom_meal.html')


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
    # Здесь будет логика оформления заказа
    return render(request, 'checkout.html')


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