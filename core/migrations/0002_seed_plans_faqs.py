from django.db import migrations

PLANS = [
    {
        "name": "Shuru", "slug": "shuru", "order": 1, "price_monthly": 0,
        "tagline": "Start selling online for free",
        "product_limit": 25, "ai_listings_per_month": 20, "staff_limit": 1, "custom_domain": False,
        "features": "Free subdomain (yourshop.dokan.ai)\n25 products\nCash on delivery\n1 courier integration\n20 AI listings a month\nOTP checkout",
    },
    {
        "name": "Growth", "slug": "growth", "order": 2, "price_monthly": 799, "is_featured": True,
        "tagline": "Everything a growing shop needs",
        "product_limit": None, "ai_listings_per_month": 200, "staff_limit": 3, "custom_domain": True,
        "features": "Custom domain with free SSL\nUnlimited products and orders\nbKash, Nagad, SSLCommerz and COD\nPathao, Steadfast and RedX\nCOD fraud shield and risk score\n200 AI listings a month\nMeta Pixel and abandoned-cart SMS",
    },
    {
        "name": "Business", "slug": "business", "order": 3, "price_monthly": 1799,
        "tagline": "Automate orders and finances",
        "product_limit": None, "ai_listings_per_month": 1000, "staff_limit": 10, "custom_domain": True,
        "features": "Everything in Growth\nFinance, P&L and VAT reports\nFacebook and Instagram catalog sync\nAI order bot on Messenger and WhatsApp\n1,000 AI listings a month\n10 staff accounts with roles",
    },
    {
        "name": "Scale", "slug": "scale", "order": 4, "price_monthly": 3999,
        "tagline": "For high-volume brands",
        "product_limit": None, "ai_listings_per_month": None, "staff_limit": None, "custom_domain": True,
        "features": "Everything in Business\nUnlimited staff and warehouses\nUnlimited AI listings\nOpen API and webhooks\nDedicated account manager\nPriority 99.9% uptime SLA credits",
    },
]

FAQS = [
    ("How does AI Snap & Sell work?", "Take a photo of your product and add a short title and price. Our AI writes the full listing in Bangla and English — description, highlights, variants, tags and SEO — in under a minute. You can edit anything before publishing."),
    ("Is there really no order limit?", "Yes. Every paid plan includes unlimited orders. We never charge per order or cap you during a big campaign."),
    ("How long is the free trial?", "Every new store gets 30 days free on any plan. Reach 10 orders and we extend it to 60 days; reach 50 orders and it becomes 90 days."),
    ("Which payments and couriers are supported?", "bKash, Nagad, SSLCommerz (cards) and cash on delivery. Couriers: Pathao, Steadfast and RedX, or your own delivery team."),
    ("How do you reduce fake COD orders?", "Buyers verify their phone with an OTP at checkout. Each order gets a risk score from delivery history across our network, and for risky orders you can ask for the delivery fee in advance via bKash or Nagad."),
    ("Can you move my shop from another builder?", "Yes — migration is free. Send us your current store link and our team will move your products and customers for you."),
    ("What does the 99.9% uptime SLA mean?", "If your store is unavailable for more than 43 minutes in a month, you get service credits on your next bill. Live status is always public on our status page."),
    ("Do I need a website if I already sell on Facebook?", "Your Facebook page is rented space — when Facebook was restricted in 2024, many sellers lost sales overnight. Your own store keeps your customers, data and orders safe, and you can keep selling on Facebook too."),
    ("Is support available in Bangla?", "Yes. Our team replies 7 days a week in Bangla and English, with a first-reply target of under 15 minutes. Every new seller also gets a free onboarding call."),
]


def seed(apps, schema_editor):
    Plan = apps.get_model("core", "Plan")
    FAQ = apps.get_model("core", "FAQ")
    for data in PLANS:
        Plan.objects.update_or_create(slug=data["slug"], defaults=data)
    for i, (q, a) in enumerate(FAQS):
        FAQ.objects.get_or_create(question=q, defaults={"answer": a, "order": i})


def unseed(apps, schema_editor):
    apps.get_model("core", "Plan").objects.filter(slug__in=[p["slug"] for p in PLANS]).delete()
    apps.get_model("core", "FAQ").objects.filter(question__in=[q for q, _ in FAQS]).delete()


class Migration(migrations.Migration):
    dependencies = [("core", "0001_initial")]
    operations = [migrations.RunPython(seed, unseed)]
