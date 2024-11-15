from django.urls import path
from .views import OrderCreateView, OrderRetrieveView

urlpatterns = [
    path('orders/', OrderCreateView.as_view(), name='order-create'),  # POST to create an order
    path('orders/<int:pk>/', OrderRetrieveView.as_view(), name='order-retrieve'),  # GET to retrieve order details
]
