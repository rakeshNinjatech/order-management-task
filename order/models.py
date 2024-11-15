from django.db import models

class Customer(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    # Assuming a field to track number of past orders for loyalty discounts
    order_count = models.IntegerField(default=0)

    def __str__(self):
        return self.name

class Item(models.Model):
    name = models.CharField(max_length=100)
    base_price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.name

class Order(models.Model):
    PENDING = 'Pending'
    CONFIRMED = 'Confirmed'
    STATUS_CHOICES = [(PENDING, 'Pending'), (CONFIRMED, 'Confirmed')]
    
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='orders')
    items = models.ManyToManyField(Item, through='OrderItem')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=PENDING)
    price_before_discount = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)
    discount_reason = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Order {self.id} - {self.status}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    item_base_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    item_gross_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    discount_reason = models.TextField(null=True, blank=True)
    quantity = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.quantity} of {self.item.name} in order {self.order.id}"

class SeasonalDiscount(models.Model):
    offerStartDate = models.DateField()
    offerEndDate = models.DateField()
    offerReason = models.CharField(max_length=150, blank=True, null=True)

    def _str__(self):
        return f"{self.offerReason} from {self.offerStartDate} to {self.offerEndDate}"


