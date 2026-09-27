"""Create a demo seller, store, catalog, customers and 30 days of orders."""

import random
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from core.models import Plan
from stores.models import Category, Coupon, Customer, Order, OrderItem, Product, Store
from stores.services.ai import generate_listing

DEMO_EMAIL = "demo@dokan.ai"
DEMO_PASSWORD = "demo12345"

PRODUCTS = [
    ("Sarees", "Tangail Handloom Cotton Saree", "টাঙ্গাইলের হাতে বোনা সুতি শাড়ি", 1450, 1850, 42, "Fashion", "Free size"),
    ("Sarees", "Jamdani Half-Silk Saree", "জামদানি হাফ সিল্ক শাড়ি", 4200, 4900, 9, "Fashion", ""),
    ("Sarees", "Rajshahi Silk Saree · Maroon", "রাজশাহী সিল্ক শাড়ি · মেরুন", 3650, None, 14, "Fashion", ""),
    ("Kurtis & Panjabi", "Block-Print Cotton Kurti", "ব্লক প্রিন্ট সুতি কুর্তি", 890, 1100, 60, "Fashion", "S, M, L, XL"),
    ("Kurtis & Panjabi", "Men's Khadi Panjabi", "ছেলেদের খাদি পাঞ্জাবি", 1650, None, 25, "Fashion", "M, L, XL, XXL"),
    ("Kurtis & Panjabi", "Embroidered Eid Three-Piece", "এমব্রয়ডারি ঈদ থ্রি-পিস", 2350, 2800, 4, "Fashion", "M, L, XL"),
    ("Home décor", "Nakshi Kantha Cushion Cover", "নকশি কাঁথা কুশন কভার", 650, None, 12, "Handicrafts", "16x16, 18x18"),
    ("Home décor", "Jute Table Runner", "পাটের টেবিল রানার", 520, 690, 30, "Home décor", ""),
    ("Home décor", "Terracotta Tea Set (6 cups)", "পোড়ামাটির চায়ের সেট", 1250, None, 0, "Handicrafts", ""),
    ("Accessories", "Jamdani Silk Dupatta", "জামদানি সিল্ক ওড়না", 980, 1200, 18, "Fashion", ""),
    ("Accessories", "Handmade Jute Tote Bag", "হাতে তৈরি পাটের ব্যাগ", 450, None, 55, "Handicrafts", ""),
    ("Accessories", "Oxidised Jhumka Earrings", "অক্সিডাইজড ঝুমকা কানের দুল", 350, 450, 3, "Fashion", ""),
]

CUSTOMERS = [
    ("Farhana Rahman", "01711234567", "House 12, Road 5, Dhanmondi", "Dhaka", True),
    ("Tanvir Hasan", "01819876543", "Sector 7, Uttara", "Dhaka", True),
    ("Nusrat Jahan", "01912345678", "Mirpur 10", "Dhaka", True),
    ("Sadia Islam", "01556677889", "Agrabad", "Chattogram", False),
    ("Rafiq Ahmed", "01678901234", "Zindabazar", "Sylhet", False),
    ("Mitu Akter", "01322334455", "Shaheb Bazar", "Rajshahi", False),
    ("Arif Chowdhury", "01744556677", "Banani DOHS", "Dhaka", True),
    ("Lamia Sultana", "01988776655", "Khulshi", "Chattogram", False),
    ("Imran Kabir", "01899001122", "Gulshan 1", "Dhaka", True),
    ("Rumana Parvin", "01633445566", "Sonadanga", "Khulna", False),
]


class Command(BaseCommand):
    help = "Seed a demo seller (demo@dokan.ai / demo12345) with the Nakshi Threads store."

    def add_arguments(self, parser):
        parser.add_argument("--reset", action="store_true", help="Delete and recreate the demo store")

    @transaction.atomic
    def handle(self, *args, **opts):
        random.seed(7)
        User = get_user_model()
        user, created = User.objects.get_or_create(
            username=DEMO_EMAIL, defaults={"email": DEMO_EMAIL, "first_name": "Ayesha", "last_name": "Siddiqua"}
        )
        if created:
            user.set_password(DEMO_PASSWORD)
            user.save()
            user.profile.phone = "01700000000"
            user.profile.save()

        existing = Store.objects.filter(slug="nakshi-threads").first()
        if existing and not opts["reset"]:
            self.stdout.write(self.style.WARNING("Demo store exists. Use --reset to recreate it."))
            return
        if existing:
            existing.orders.all().delete()
            existing.delete()

        store = Store.objects.create(
            owner=user, name="Nakshi Threads", slug="nakshi-threads", category="Fashion",
            tagline="Handwoven sarees, kurtis and crafts from across Bangladesh",
            brand_color="#1E7F5C", theme="boutique", phone="01700000000", email=DEMO_EMAIL,
            address="Shop 14, Level 3, Bashundhara City, Dhaka", facebook_url="https://facebook.com/",
            plan=Plan.objects.filter(slug="growth").first(),
            enabled_payments="cod,bkash,nagad,sslcommerz",
        )
        store.created_at = timezone.now() - timedelta(days=34)
        store.trial_ends_at = store.created_at + timedelta(days=60)
        store.save()

        cats = {}
        products = []
        for cat, title, title_bn, price, compare, stock, kind, variants in PRODUCTS:
            if cat not in cats:
                cats[cat] = Category.objects.create(store=store, name=cat)
            listing = generate_listing(title, price, kind)
            p = Product.objects.create(
                store=store, category=cats[cat], title=title, title_bn=title_bn, price=price,
                compare_at_price=compare, cost_price=round(price * 0.58), stock=stock,
                description_en=listing["description_en"], description_bn=listing["description_bn"],
                highlights="\n".join(listing["highlights"]), variants=variants,
                tags=", ".join(listing["tags"]), seo_title=listing["seo_title"],
                seo_description=listing["seo_description"], ai_generated=True,
                sku=f"NT-{len(products) + 101}",
            )
            products.append(p)

        customers = [
            Customer.objects.create(store=store, name=n, phone=ph, address=a, city=c, phone_verified=v)
            for n, ph, a, c, v in CUSTOMERS
        ]

        Coupon.objects.create(store=store, code="EID20", percent_off=20, min_order=1500, usage_limit=200, times_used=37)
        Coupon.objects.create(store=store, code="WELCOME100", amount_off=100, min_order=800, times_used=12)
        Coupon.objects.create(store=store, code="BOISHAKH", percent_off=15, is_active=False)

        now = timezone.now()
        statuses = ["delivered"] * 9 + ["shipped"] * 3 + ["packed", "confirmed", "returned", "cancelled"]
        in_stock = [p for p in products if p.stock > 0]
        count = 0
        for day in range(30, -1, -1):
            for _ in range(random.choice([0, 1, 1, 2, 2, 3, 4])):
                cust = random.choice(customers)
                picks = random.sample(in_stock, random.choice([1, 1, 2]))
                inside = cust.city == "Dhaka"
                fee = Decimal(store.delivery_fee_dhaka if inside else store.delivery_fee_outside)
                status = "pending" if day == 0 else random.choice(statuses)
                method = random.choice(["cod", "cod", "cod", "bkash", "bkash", "nagad", "sslcommerz"])
                risk = random.choice([8, 12, 18, 24, 35]) if cust.phone_verified else random.choice([22, 40, 55, 68, 74])
                order = Order.objects.create(
                    store=store, customer=cust, status=status, payment_method=method,
                    payment_status="paid" if method != "cod" or status == "delivered" else "unpaid",
                    courier=random.choice(["pathao", "steadfast", "redx"]) if status in ("shipped", "delivered", "returned") else "",
                    tracking_code=f"TRK{random.randint(100000, 999999)}" if status in ("shipped", "delivered") else "",
                    shipping_name=cust.name, shipping_phone=cust.phone, shipping_address=cust.address,
                    shipping_city=cust.city, inside_dhaka=inside, delivery_fee=fee, risk_score=risk,
                    otp_verified=cust.phone_verified, source=random.choice(["store", "store", "store", "messenger", "whatsapp", "manual"]),
                )
                for p in picks:
                    OrderItem.objects.create(
                        order=order, product=p, title=p.title, unit_price=p.price, quantity=random.choice([1, 1, 2]),
                        variant=p.variant_list[0] if p.variant_list else "",
                    )
                order.recalculate()
                order.save()
                stamp = now - timedelta(days=day, hours=random.randint(0, 10), minutes=random.randint(0, 59))
                Order.objects.filter(pk=order.pk).update(created_at=stamp)
                count += 1
        for c in customers:
            c.loyalty_points = sum(int(o.total // 100) for o in c.orders.all())
            c.save(update_fields=["loyalty_points"])

        self.stdout.write(self.style.SUCCESS(
            f"Demo ready: {len(products)} products, {len(customers)} customers, {count} orders.\n"
            f"  Store:     /s/nakshi-threads/\n  Dashboard: /dashboard/  ({DEMO_EMAIL} / {DEMO_PASSWORD})"
        ))
