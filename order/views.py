from rest_framework.generics import CreateAPIView, RetrieveAPIView
from .models import Order
from .serializer import OrderSerializer,OrderViewSerializer
from rest_framework.response import Response
from rest_framework import status
from .utils import mock_payment, send_mock_notification

class OrderCreateView(CreateAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer

    def create(self, request, *args, **kwargs):
        # Ensure customer is included in the request
        if not request.data.get('customer_id'):
            return Response({"error": "Customer ID is required."}, status=status.HTTP_400_BAD_REQUEST)
        
        if not request.data.get('items'):
            return Response({"error": "At least one item is required."}, status=status.HTTP_400_BAD_REQUEST)
        
        for item in request.data.get('items', []):
            if not item.get('item'):
                return Response({"error": "Invalid data."}, status=status.HTTP_400_BAD_REQUEST)
            if not item.get('quantity'):
                return Response({"error": "Invalid data."}, status=status.HTTP_400_BAD_REQUEST)
            if not isinstance(item.get('quantity'),int):
                return Response({"error": "Invalid data."}, status=status.HTTP_400_BAD_REQUEST)
            if item.get('quantity', 0) < 0:
                return Response({"error": "Item quantity cannot be negative."}, status=status.HTTP_400_BAD_REQUEST)


        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Save the order and link it to the customer
        order = serializer.save()

        # Mock payment and notification
        if mock_payment(order):
            order.status = Order.CONFIRMED
            send_mock_notification(order)
            order.save()

        # Customize response to include customer information
        return Response({
            "order_id": order.id,
            "status": order.status,
            "total_price": order.total_price,
            "customer_id": order.customer.id,
            "message": "Order created successfully and payment confirmed."
        }, status=status.HTTP_201_CREATED)

class OrderRetrieveView(RetrieveAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderViewSerializer
