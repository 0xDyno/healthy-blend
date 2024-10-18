# core/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.views import View
from django.utils.decorators import method_decorator
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import User, Ingredient, Product, Order, OrderProduct, History
from .serializers import UserSerializer, IngredientSerializer, ProductSerializer, OrderSerializer, HistorySerializer


class IsAdminUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.role == 'admin'


class IsManagerUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.role == 'manager'


class IsTableUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.role == 'table'

# API ViewSets


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdminUser]


class IngredientViewSet(viewsets.ModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = [IsAdminUser]


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAdminUser]

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.IsAuthenticated()]
        return super().get_permissions()

    @action(detail=False, methods=['post'], permission_classes=[IsTableUser])
    def custom(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


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

def home(request):
    return render(request, 'home.html')


def user_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            return render(request, 'login.html', {'error': 'Invalid credentials'})
    return render(request, 'login.html')


@login_required
def user_logout(request):
    logout(request)
    return redirect('home')


@login_required
def menu(request):
    products = Product.objects.all()
    return render(request, 'menu.html', {'products': products})


@login_required
def cart(request):
    # В будущем здесь будет логика получения корзины пользователя
    cart_items = []
    total_price = 0
    return render(request, 'cart.html', {'cart_items': cart_items, 'total_price': total_price})


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
def orders(request):
    if request.user.role != 'manager':
        return redirect('home')
    orders = Order.objects.all().order_by('-order_time')
    order_statuses = Order.STATUS_CHOICES
    return render(request, 'orders.html', {'orders': orders, 'order_statuses': order_statuses})


@login_required
@require_POST
def update_order_status(request):
    order_id = request.POST.get('order_id')
    new_status = request.POST.get('status')
    order = get_object_or_404(Order, id=order_id)
    if request.user.role == 'manager':
        order.order_status = new_status
        order.save()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False}, status=403)
