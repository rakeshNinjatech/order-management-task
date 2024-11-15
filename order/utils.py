from datetime import date
from decimal import Decimal
from .models import SeasonalDiscount

def apply_discounts(order):
    try:
        # Calculate initial total price by iterating over OrderItem instances
        total_price = sum(order_item.item.base_price * order_item.quantity for order_item in order.orderitem_set.all())
        order.price_before_discount = total_price


        # Volume-Based Discount
        for order_item in order.orderitem_set.all():
            if order_item.quantity > 10:
                order_item.item_base_price = order_item.item.base_price
                order_item.item_gross_cost = (order_item.item.base_price * order_item.quantity) - (order_item.item.base_price * order_item.quantity) * Decimal('0.10')
                order_item.discount_reason = (order_item.discount_reason or "") +  f"Volume based discount of 10% for item {order_item.item.name}"
                total_price -= order_item.item.base_price * order_item.quantity * Decimal('0.10')  # 10% discount on this item
            else:
                order_item.item_base_price = order_item.item.base_price
                order_item.item_gross_cost = order_item.item.base_price * order_item.quantity
            order_item.save()


        if date.today() >= date(order.created_at.year, 11, 10) and date.today() <= date(order.created_at.year, 12, 31): #10th Nov to 31st Dec of Current Year(Seasonal Offer)
            total_price *= Decimal('0.85')
            order.discount_reason =(order.discount_reason or "") + "Seasonal Discount of 15%."
        
        if order.customer.order_count > 5:
            total_price *= Decimal('0.95')  # 5% loyalty discount
            order.discount_reason = (order.discount_reason or "") + "Loyalty Discount of 5%."

        order.save()

        return total_price, True
    except Exception as e:
        return 0, False

def mock_payment(order):
    print(f"Payment Sucessful for order ID: {order.id}")
    return True

def send_mock_notification(order):
    # Simulate sending a notification to customer
    print(f"Notification sent for Order ID {order.id}, Total Price: {order.total_price}")

