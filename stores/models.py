import secrets
from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify

TRIAL_DAYS = 30

COURIERS = [("pathao", "Pathao"), ("steadfast", "Steadfast"), ("redx", "RedX"), ("self", "Own delivery")]
PAYMENT_METHODS = [
    ("cod", "Cash on delivery"),
    ("bkash", "bKash"),
    ("nagad", "Nagad"),
    ("sslcommerz", "Card / SSLCommerz"),
]
THEMES = [("bazaar", "Bazaar"), ("minimal", "Minimal"), ("boutique", "Boutique")]


def unique_slug(model, value, instance=None, field="slug", **scope):
    base = slugify(value)[:50] or "item"
    slug, n = base, 2
    qs = model.objects.filter(**scope)
    if instance and instance.pk:
        qs = qs.exclude(pk=instance.pk)
    while qs.filter(**{field: slug}).exists():
        slug = f"{base}-{n}"
        n += 1
    return slug


class Store(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="stores")
    name = models.CharField(max_length=80)
    slug = models.SlugField(unique=True, help_text="Used in your free subdomain")
    tagline = models.CharField(max_length=140, blank=True)
    category = models.CharField(max_length=60, blank=True)
    logo = models.ImageField(upload_to="logos/", blank=True)
    brand_color = models.CharField(max_length=7, default="#1E7F5C")
    theme = models.CharField(max_length=20, choices=THEMES, default="bazaar")
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    address = models.CharField(max_length=200, blank=True)
    facebook_url = models.URLField(blank=True)
    custom_domain = models.CharField(max_length=120, blank=True)
    delivery_fee_dhaka = models.PositiveIntegerField(default=60)
    delivery_fee_outside = models.PositiveIntegerField(default=120)
    advance_threshold = models.PositiveIntegerField(
        default=60, help_text="Ask for delivery-fee advance when the risk score is at or above this (0–100)"
    )
    otp_checkout = models.BooleanField(default=True)
    enabled_payments = models.CharField(max_length=80, default="cod,bkash,nagad")
    enabled_couriers = models.CharField(max_length=80, default="pathao,steadfast,redx")
    plan = models.ForeignKey("core.Plan", on_delete=models.PROTECT, null=True, blank=True)
    billing_cycle = models.CharField(max_length=10, choices=[("monthly", "Monthly"), ("annual", "Annual")], default="monthly")
    trial_ends_at = models.DateTimeField(null=True, blank=True)
    is_live = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slug(Store, self.name, self)
        if not self.trial_ends_at:
            self.trial_ends_at = timezone.now() + timedelta(days=TRIAL_DAYS)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("storefront:home", args=[self.slug])

    @property
    def subdomain(self):
        return f"{self.slug}.dokan.ai"

    @property
    def payment_list(self):
        return [p for p in self.enabled_payments.split(",") if p]

    @property
    def payment_choices(self):
        return [(k, v) for k, v in PAYMENT_METHODS if k in self.payment_list]

    @property
    def courier_list(self):
        return [c for c in self.enabled_couriers.split(",") if c]

    @property
    def trial_days_left(self):
        if not self.trial_ends_at:
            return 0
        return max(0, (self.trial_ends_at - timezone.now()).days)

    def extend_trial_for_milestones(self):
        """Free period: 30 days, extended to 60 and 90 as sellers reach 10 and 50 orders."""
        count = self.orders.exclude(status=Order.Status.CANCELLED).count()
        target_days = 90 if count >= 50 else 60 if count >= 10 else TRIAL_DAYS
        target = self.created_at + timedelta(days=target_days)
        if self.trial_ends_at and target > self.trial_ends_at:
            self.trial_ends_at = target
            self.save(update_fields=["trial_ends_at"])

    def ai_listings_this_month(self):
        start = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        return self.products.filter(ai_generated=True, created_at__gte=start).count()

    def ai_quota(self):
        if self.plan:
            return self.plan.ai_listings_per_month
        return 20


class Category(models.Model):
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name="categories")
    name = models.CharField(max_length=60)
    slug = models.SlugField()

    class Meta:
        ordering = ["name"]
        unique_together = [("store", "slug")]
        verbose_name_plural = "categories"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slug(Category, self.name, self, store=self.store)
        super().save(*args, **kwargs)


class Product(models.Model):
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name="products")
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name="products")
    title = models.CharField(max_length=140)
    title_bn = models.CharField("Title (Bangla)", max_length=140, blank=True)
    slug = models.SlugField(max_length=160)
    sku = models.CharField(max_length=40, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=0)
    compare_at_price = models.DecimalField(max_digits=10, decimal_places=0, null=True, blank=True)
    cost_price = models.DecimalField(max_digits=10, decimal_places=0, null=True, blank=True)
    stock = models.PositiveIntegerField(default=0)
    low_stock_threshold = models.PositiveIntegerField(default=5)
    image = models.ImageField(upload_to="products/", blank=True)
    description_en = models.TextField("Description (English)", blank=True)
    description_bn = models.TextField("Description (Bangla)", blank=True)
    highlights = models.TextField(blank=True, help_text="One highlight per line")
    variants = models.CharField(max_length=200, blank=True, help_text="Comma separated, e.g. S, M, L")
    tags = models.CharField(max_length=240, blank=True, help_text="Comma separated")
    seo_title = models.CharField(max_length=70, blank=True)
    seo_description = models.CharField(max_length=170, blank=True)
    is_active = models.BooleanField(default=True)
    ai_generated = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        unique_together = [("store", "slug")]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slug(Product, self.title, self, store=self.store)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("storefront:product", args=[self.store.slug, self.slug])

    @property
    def is_low_stock(self):
        return self.stock <= self.low_stock_threshold

    @property
    def discount_pct(self):
        if self.compare_at_price and self.compare_at_price > self.price:
            return round((1 - self.price / self.compare_at_price) * 100)
        return 0

    @property
    def tag_list(self):
        return [t.strip() for t in self.tags.split(",") if t.strip()]

    @property
    def variant_list(self):
        return [v.strip() for v in self.variants.split(",") if v.strip()]

    @property
    def highlight_list(self):
        return [h.strip() for h in self.highlights.splitlines() if h.strip()]

    @property
    def initials(self):
        words = [w for w in self.title.split() if w[:1].isalnum()]
        return "".join(w[0] for w in words[:2]).upper() or "?"


class Customer(models.Model):
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name="customers")
    name = models.CharField(max_length=120)
    phone = models.CharField(max_length=20)
    email = models.EmailField(blank=True)
    address = models.CharField(max_length=240, blank=True)
    city = models.CharField(max_length=60, blank=True)
    phone_verified = models.BooleanField(default=False)
    loyalty_points = models.PositiveIntegerField(default=0)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        unique_together = [("store", "phone")]

    def __str__(self):
        return f"{self.name} ({self.phone})"

    @property
    def segment(self):
        count = getattr(self, "order_count", None)
        if count is None:
            count = self.orders.count()
        if count >= 5:
            return "VIP"
        if count >= 2:
            return "Repeat"
        return "New"


class Coupon(models.Model):
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name="coupons")
    code = models.CharField(max_length=30)
    percent_off = models.PositiveSmallIntegerField(null=True, blank=True)
    amount_off = models.PositiveIntegerField(null=True, blank=True)
    min_order = models.PositiveIntegerField(default=0)
    usage_limit = models.PositiveIntegerField(null=True, blank=True)
    times_used = models.PositiveIntegerField(default=0)
    expires_at = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = [("store", "code")]
        ordering = ["code"]

    def __str__(self):
        return self.code

    def save(self, *args, **kwargs):
        self.code = self.code.upper().strip()
        super().save(*args, **kwargs)

    def is_valid_for(self, subtotal):
        if not self.is_active:
            return False, "This coupon is not active."
        if self.expires_at and self.expires_at < timezone.localdate():
            return False, "This coupon has expired."
        if self.usage_limit is not None and self.times_used >= self.usage_limit:
            return False, "This coupon has reached its usage limit."
        if subtotal < self.min_order:
            return False, f"Minimum order for this coupon is ৳{self.min_order}."
        return True, ""

    def discount_for(self, subtotal):
        subtotal = Decimal(subtotal)
        if self.percent_off:
            return min(subtotal, (subtotal * self.percent_off / 100).quantize(Decimal("1")))
        if self.amount_off:
            return min(subtotal, Decimal(self.amount_off))
        return Decimal(0)

    @property
    def label(self):
        return f"{self.percent_off}% off" if self.percent_off else f"৳{self.amount_off} off"


class Order(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        CONFIRMED = "confirmed", "Confirmed"
        PACKED = "packed", "Packed"
        SHIPPED = "shipped", "Shipped"
        DELIVERED = "delivered", "Delivered"
        RETURNED = "returned", "Returned"
        CANCELLED = "cancelled", "Cancelled"

    class PaymentStatus(models.TextChoices):
        UNPAID = "unpaid", "Unpaid"
        PARTIAL = "partial", "Advance paid"
        PAID = "paid", "Paid"
        REFUNDED = "refunded", "Refunded"

    FLOW = ["pending", "confirmed", "packed", "shipped", "delivered"]

    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name="orders")
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name="orders")
    number = models.CharField(max_length=20, unique=True, editable=False)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default="cod")
    payment_status = models.CharField(max_length=20, choices=PaymentStatus.choices, default=PaymentStatus.UNPAID)
    transaction_id = models.CharField(max_length=60, blank=True)
    courier = models.CharField(max_length=20, choices=COURIERS, blank=True)
    tracking_code = models.CharField(max_length=60, blank=True)
    shipping_name = models.CharField(max_length=120)
    shipping_phone = models.CharField(max_length=20)
    shipping_address = models.CharField(max_length=240)
    shipping_city = models.CharField(max_length=60)
    inside_dhaka = models.BooleanField(default=True)
    subtotal = models.DecimalField(max_digits=12, decimal_places=0, default=0)
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=0, default=0)
    discount = models.DecimalField(max_digits=10, decimal_places=0, default=0)
    total = models.DecimalField(max_digits=12, decimal_places=0, default=0)
    advance_required = models.DecimalField(max_digits=10, decimal_places=0, default=0)
    coupon = models.ForeignKey(Coupon, on_delete=models.SET_NULL, null=True, blank=True)
    risk_score = models.PositiveSmallIntegerField(default=0)
    otp_verified = models.BooleanField(default=False)
    source = models.CharField(max_length=20, default="store", choices=[
        ("store", "Website"), ("messenger", "Messenger"), ("whatsapp", "WhatsApp"), ("manual", "Manual"),
    ])
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"#{self.number}"

    def save(self, *args, **kwargs):
        if not self.number:
            self.number = f"{timezone.localdate():%y%m}{secrets.randbelow(900000) + 100000}"
            while Order.objects.filter(number=self.number).exists():
                self.number = f"{timezone.localdate():%y%m}{secrets.randbelow(900000) + 100000}"
        super().save(*args, **kwargs)

    def recalculate(self):
        self.subtotal = sum((i.line_total for i in self.items.all()), Decimal(0))
        self.total = max(Decimal(0), self.subtotal + self.delivery_fee - self.discount)

    @property
    def risk_level(self):
        if self.risk_score >= 60:
            return "high"
        if self.risk_score >= 30:
            return "medium"
        return "low"

    @property
    def progress_steps(self):
        current = self.FLOW.index(self.status) if self.status in self.FLOW else -1
        return [
            {"key": k, "label": dict(self.Status.choices)[k], "done": i <= current, "current": i == current}
            for i, k in enumerate(self.FLOW)
        ]

    @property
    def due_on_delivery(self):
        if self.payment_status == self.PaymentStatus.PAID:
            return Decimal(0)
        paid = self.advance_required if self.payment_status == self.PaymentStatus.PARTIAL else 0
        return max(Decimal(0), self.total - paid)


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    title = models.CharField(max_length=140)
    variant = models.CharField(max_length=60, blank=True)
    unit_price = models.DecimalField(max_digits=10, decimal_places=0)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.quantity} × {self.title}"

    @property
    def line_total(self):
        return self.unit_price * self.quantity
