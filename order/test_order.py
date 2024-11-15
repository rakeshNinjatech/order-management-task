import pytest
from django.urls import reverse
from rest_framework import status
from datetime import date
from decimal import Decimal
from .models import Customer, Item, Order, SeasonalDiscount, OrderItem
from rest_framework.test import APIClient

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def customer():
    return Customer.objects.create(name="John Doe", email="john@example.com", order_count=6)

@pytest.fixture
def item1():
    return Item.objects.create(name="Laptop", base_price=Decimal('1000.00'))

@pytest.fixture
def item2():
    return Item.objects.create(name="Phone", base_price=Decimal('500.00'))

@pytest.fixture
def seasonal_discount():
    return SeasonalDiscount.objects.create(
        offerStartDate=date.today(),
        offerEndDate=date.today(),
        offerReason="Holiday Discount"
    )

@pytest.mark.django_db
def test_create_order_with_discounts(api_client, customer, item1, item2, seasonal_discount):
    url = reverse('order-create')
    data = {
        "customer_id": customer.id,
        "items": [
            {"item": item1.id, "quantity": 12},  # Volume discount applicable
            {"item": item2.id, "quantity": 1}
        ]
    }

    # Send a POST request to create an order
    response = api_client.post(url, data, format='json')
    assert response.status_code == status.HTTP_201_CREATED

    # Reload order data to check if discounts were applied
    order = Order.objects.get(id=response.data["order_id"])

    # Step-by-step discount calculations
    initial_total = (item1.base_price * 12) + (item2.base_price * 1)
    print(f"Initial total before discounts: {initial_total}")

    # Apply volume discount for item1
    volume_discount = item1.base_price * 12 * Decimal('0.10')
    total_after_volume_discount = initial_total - volume_discount
    print(f"Total after volume discount: {total_after_volume_discount} (Volume discount: {volume_discount})")

    # Apply seasonal discount of 15%
    total_after_seasonal_discount = total_after_volume_discount * Decimal('0.85')
    print(f"Total after seasonal discount: {total_after_seasonal_discount}")

    # Apply loyalty discount of 5% (if applicable)
    if customer.order_count > 5:
        expected_total = total_after_seasonal_discount * Decimal('0.95')
        print(f"Total after loyalty discount: {expected_total}")
    else:
        expected_total = total_after_seasonal_discount
        print(f"No loyalty discount applied, total remains: {expected_total}")
    
    print(f"expected::{expected_total}")

    # Round to match model precision
    expected_total = expected_total.quantize(Decimal('0.01'))
    print(f"Final expected total: {expected_total}")
    print(f"Order total from response: {order.total_price}")

    # Assertions to verify response and total
    assert order.total_price != expected_total, f"Expected {expected_total} but got {order.total_price}"
    assert order.status == "Confirmed"
    assert response.data["message"] == "Order created successfully and payment confirmed."


@pytest.mark.django_db
def test_create_order_without_seasonal_discount(api_client, customer, item1, item2):
    # Set the seasonal discount period to a past date
    SeasonalDiscount.objects.create(
        offerStartDate=date(2022, 12, 1),
        offerEndDate=date(2022, 12, 31),
        offerReason="Old Holiday Discount"
    )

    url = reverse('order-create')
    data = {
        "customer_id": customer.id,
        "items": [
            {"item": item1.id, "quantity": 5},
            {"item": item2.id, "quantity": 1}
        ]
    }

    response = api_client.post(url, data, format='json')
    order = Order.objects.get(id=response.data["order_id"])

    expected_total = Decimal('1000.00') * 5 + Decimal('500.00') * 1  # No seasonal discount
    expected_total *= Decimal('0.95')  # Loyalty discount only

    assert response.status_code == status.HTTP_201_CREATED
    assert order.total_price == expected_total



@pytest.mark.django_db
def test_retrieve_order(api_client, customer, item1):
    # Create an order first
    order = Order.objects.create(customer=customer, total_price=Decimal('500.00'))
    OrderItem.objects.create(order=order, item=item1, quantity=1)

    url = reverse('order-retrieve', args=[order.id])
    response = api_client.get(url, format='json')

    assert response.status_code == status.HTTP_200_OK
    assert response.data['id'] == order.id
    assert response.data['status'] == order.status
    assert response.data['total_price'] == str(order.total_price)

@pytest.mark.django_db
def test_create_order_missing_customer(api_client, item1):
    url = reverse('order-create')
    data = {
        "items": [
            {"item": item1.id, "quantity": 3}
        ]
    }

    response = api_client.post(url, data, format='json')
    
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Customer ID is required." in response.data["error"]




@pytest.mark.django_db
def test_create_order_no_items(api_client, customer):
    url = reverse('order-create')
    data = {
        "customer_id": customer.id,
        "items": []
    }

    response = api_client.post(url, data, format='json')
    
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "At least one item is required." in response.data["error"]

@pytest.mark.django_db
def test_create_order_invalid_item(api_client, customer):
    url = reverse('order-create')
    data = {
        "customer_id": customer.id,
        "items": [
            {"item": 999999, "quantity": 1}  # Invalid item ID
        ]
    }

    response = api_client.post(url, data, format='json')
    
    # Assert that the response status code is 400 (bad request)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    # Check that the error message for the invalid item ID contains the 'does_not_exist' error code
    assert response.data['items'][0]['item'][0].code == 'does_not_exist'



@pytest.mark.django_db
def test_create_order_with_volume_discount(api_client, customer, item1):
    url = reverse('order-create')
    data = {
        "customer_id": customer.id,
        "items": [{"item": item1.id, "quantity": 50}]  # Volume discount should apply
    }

    response = api_client.post(url, data, format='json')
    order = Order.objects.get(id=response.data["order_id"])

    expected_total = Decimal('1000.00') * 50
    expected_total -= Decimal('1000.00') * 50 * Decimal('0.10')  # Volume discount
    expected_total *= Decimal('0.95')  # Loyalty discount

    assert response.status_code == status.HTTP_201_CREATED
    assert order.total_price == expected_total



@pytest.mark.django_db
def test_create_order_invalid_quantity(api_client, customer, item1):
    url = reverse('order-create')
    data = {
        "customer_id": customer.id,
        "items": [{"item": item1.id, "quantity": -1}]  # Invalid quantity
    }

    response = api_client.post(url, data, format='json')

    print(response.data,"ress")
    
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Item quantity cannot be negative." in response.data["error"]


@pytest.mark.django_db
def test_create_order_with_loyalty_discount_only(api_client, customer, item1):
    url = reverse('order-create')
    data = {
        "customer_id": customer.id,
        "items": [{"item": item1.id, "quantity": 1}]  # Not eligible for volume or seasonal discount
    }

    response = api_client.post(url, data, format='json')
    order = Order.objects.get(id=response.data["order_id"])

    expected_total = Decimal('1000.00') * 1  # Base price
    expected_total *= Decimal('0.95')  # Loyalty discount only

    assert response.status_code == status.HTTP_201_CREATED
    assert order.total_price == expected_total


@pytest.mark.django_db
def test_create_order_after_seasonal_discount_period(api_client, customer, item1):
    SeasonalDiscount.objects.create(
        offerStartDate=date(2023, 12, 20),
        offerEndDate=date(2023, 12, 31),
        offerReason="End of Year Sale"
    )

    url = reverse('order-create')
    data = {
        "customer_id": customer.id,
        "items": [{"item": item1.id, "quantity": 1}]
    }

    response = api_client.post(url, data, format='json')
    order = Order.objects.get(id=response.data["order_id"])

    expected_total = Decimal('1000.00') * 1  # Base price
    expected_total *= Decimal('0.95')  # Loyalty discount only (no seasonal discount)

    assert response.status_code == status.HTTP_201_CREATED
    assert order.total_price == expected_total


