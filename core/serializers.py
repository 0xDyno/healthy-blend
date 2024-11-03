# serializers.py

from rest_framework import serializers

from core.models import OrderHistory, Order, Purchase


class OrderHistorySerializer(serializers.ModelSerializer):
    user_last_update_name = serializers.CharField(source='user_last_update.username', read_only=True)
    created_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")

    class Meta:
        model = OrderHistory
        fields = ['id', 'order_status', 'order_type', 'payment_type', 'user_last_update_name',
                 'tax', 'service', 'base_price', 'total_price', 'is_paid', 'is_refunded',
                 'public_note', 'private_note', 'created_at', 'payment_id']


class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['id', 'order_status', 'created_at']


class PurchaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Purchase
        fields = '__all__'
