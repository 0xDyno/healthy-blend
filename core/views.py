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