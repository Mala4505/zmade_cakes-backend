from decimal import Decimal
from django.core.management.base import BaseCommand
from django.utils import timezone
from orders.models import Order, CollateralItem


class Command(BaseCommand):
    help = "Seed test orders"

    def handle(self, *args, **options):
        if Order.objects.exists():
            self.stdout.write("Orders already exist, skipping seed.")
            return

        orders_data = [
            {
                "customer_name": "Fatima Al-Sabah",
                "phone": "99991234",
                "email": "",
                "area": "Jabriya",
                "address": "Block 3, Street 15, House 22",
                "pickup_or_delivery": "delivery",
                "items": [
                    {
                        "cake_type": "Birthday Cake",
                        "flavor": "Vanilla Berry",
                        "size": "8 inch",
                        "quantity": 1,
                        "price": "25.0",
                        "notes": "Write Happy Birthday Mama in gold",
                    }
                ],
                "delivery_date": timezone.now().date(),
                "delivery_time": "afternoon",
                "status": "pending",
                "payment_status": "unpaid",
                "admin_notes": "",
                "customer_notes": "Please deliver to back door",
                "collateral": [],
            },
            {
                "customer_name": "Mohammed Ali",
                "phone": "66667777",
                "email": "",
                "area": "Salwa",
                "address": "Block 1, Street 4, House 10",
                "pickup_or_delivery": "pickup",
                "items": [
                    {
                        "cake_type": "Cupcakes",
                        "flavor": "Red Velvet",
                        "size": "Dozen",
                        "quantity": 2,
                        "price": "18.0",
                        "notes": "",
                    },
                    {
                        "cake_type": "Custom Cake",
                        "flavor": "Chocolate Fudge",
                        "size": "10 inch",
                        "quantity": 1,
                        "price": "35.0",
                        "notes": "Blue theme",
                    },
                ],
                "delivery_date": timezone.now().date(),
                "delivery_time": "morning",
                "status": "preparing",
                "payment_status": "paid",
                "admin_notes": "",
                "customer_notes": "",
                "collateral": [
                    {"item_name": "Glass stand", "deposit_amount": Decimal("10"), "return_required": True},
                ],
            },
        ]

        for data in orders_data:
            collateral = data.pop("collateral", [])
            payment_status = data.get("payment_status", "unpaid")
            if payment_status == "paid":
                data["payment_date"] = timezone.now()
            order = Order.objects.create(**data)
            for c in collateral:
                CollateralItem.objects.create(order=order, **c)

        self.stdout.write(self.style.SUCCESS(f"Created {len(orders_data)} orders."))
