from rest_framework import serializers
from .models import Order, OrderItem,Customer
from .utils import apply_discounts
from decimal import Decimal


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ['quantity','item','item_base_price', 'item_gross_cost', 'discount_reason']

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)
    customer_id = serializers.PrimaryKeyRelatedField(queryset=Customer.objects.all(), source='customer')

    class Meta:
        model = Order
        fields = ['id', 'customer_id', 'items', 'status', 'total_price', 'discount_reason', 'price_before_discount','created_at']
        read_only_fields = ['status', 'total_price', 'created_at']

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        customer = validated_data.pop('customer')
        
        # Create order with the associated customer
        order = Order.objects.create(customer=customer, **validated_data)
        order.customer.order_count +=1
        order.customer.save()

        
        for item_data in items_data:
            OrderItem.objects.create(order=order, **item_data)
        
        # Calculate the total price and apply discounts (including loyalty discount)
        order.total_price, status = apply_discounts(order)
        if not status:
            raise serializers.ValidationError({'error': 'Something went wrong.'})

        order.save()
        
        return order
    
class OrderItemViewSerializer(serializers.ModelSerializer):
    item = serializers.CharField(read_only=True)
    class Meta:
        model = OrderItem
        fields = ['quantity','item','item_base_price', 'item_gross_cost', 'discount_reason']
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if representation.get('discount_reason'):
            representation['item_total_cost_without_discount'] = Decimal(representation.get('item_base_price')) * Decimal(representation.get('quantity'))

        return representation
    
class OrderViewSerializer(serializers.ModelSerializer):
    order_items = OrderItemViewSerializer(many=True,source="orderitem_set")
    class Meta:
        model = Order
        fields = ['id', 'order_items', 'status', 'total_price', 'created_at','discount_reason','price_before_discount']
        read_only_fields = ['status', 'total_price', 'created_at','discount_reason']

    def to_representation(self, instance):
        # Get the default representation from the serializer
        representation = super().to_representation(instance)
        total_p = representation['total_price']
        b_discount = representation['price_before_discount']
        representation['discounted_amount'] = Decimal(b_discount) - Decimal(total_p)
        return representation