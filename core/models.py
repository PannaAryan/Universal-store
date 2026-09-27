from django.db import models


class Plan(models.Model):
    """Subscription plan shown on the pricing page and used for billing."""

    name = models.CharField(max_length=40)
    slug = models.SlugField(unique=True)
    tagline = models.CharField(max_length=120)
    price_monthly = models.PositiveIntegerField(help_text="Price in BDT per month")
    is_featured = models.BooleanField(default=False)
    order = models.PositiveSmallIntegerField(default=0)
    product_limit = models.PositiveIntegerField(null=True, blank=True, help_text="Blank = unlimited")
    ai_listings_per_month = models.PositiveIntegerField(null=True, blank=True, help_text="Blank = unlimited")
    staff_limit = models.PositiveIntegerField(null=True, blank=True, help_text="Blank = unlimited")
    custom_domain = models.BooleanField(default=False)
    features = models.TextField(help_text="One feature per line")

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return self.name

    @property
    def feature_list(self):
        return [f.strip() for f in self.features.splitlines() if f.strip()]

    @property
    def price_annual_monthly(self):
        """Effective monthly price on the annual plan (2 months free)."""
        return round(self.price_monthly * 10 / 12)

    @property
    def price_annual(self):
        return self.price_monthly * 10

    @property
    def is_free(self):
        return self.price_monthly == 0


class Lead(models.Model):
    """Demo bookings, contact messages, migration and partnership requests."""

    class Kind(models.TextChoices):
        DEMO = "demo", "Book a demo"
        CONTACT = "contact", "General question"
        MIGRATION = "migration", "Free migration"
        PARTNER = "partner", "Partnership"
        INVESTOR = "investor", "Investor enquiry"

    kind = models.CharField(max_length=20, choices=Kind.choices, default=Kind.DEMO)
    name = models.CharField(max_length=120)
    phone = models.CharField(max_length=30)
    email = models.EmailField(blank=True)
    business_name = models.CharField(max_length=120, blank=True)
    facebook_page = models.URLField(blank=True)
    category = models.CharField(max_length=60, blank=True)
    message = models.TextField(blank=True)
    handled = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.get_kind_display()} · {self.name}"


class NewsletterSubscriber(models.Model):
    email = models.EmailField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.email


class FAQ(models.Model):
    question = models.CharField(max_length=200)
    answer = models.TextField()
    order = models.PositiveSmallIntegerField(default=0)
    is_published = models.BooleanField(default=True)

    class Meta:
        ordering = ["order"]
        verbose_name = "FAQ"
        verbose_name_plural = "FAQs"

    def __str__(self):
        return self.question
