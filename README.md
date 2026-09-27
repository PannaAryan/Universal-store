# Dokan AI — Take a photo. Get a store.

An AI e-commerce store builder for Bangladesh's 2 lakh+ F-commerce sellers, built with Django.
A seller uploads a product photo and gets a working online store with orders, couriers and
bKash / Nagad / SSLCommerz / COD payments.

## What's inside

**Marketing site** (`core`): home, features, AI Snap & Sell with a live "try it" demo, pricing
(monthly/annual toggle), competitor comparison, about + roadmap + go-to-market, investor overview
(market, TAM/SAM/SOM, unit economics, 5-year ARR, risks, use of funds), contact/demo booking,
help center + FAQ, public status page, terms / privacy / refund & SLA, newsletter.

**Seller dashboard** (`/dashboard/`): 3-step onboarding wizard with live brand preview, overview
KPIs + 14-day sales chart + launch checklist + low-stock alerts, products with **AI Snap & Sell**
(photo → Bangla & English listing, highlights, variants, tags, SEO), orders with status flow,
couriers (Pathao, Steadfast, RedX), payment status and tracking, manual Messenger/WhatsApp orders,
fraud-shield risk scores, customers with New/Repeat/VIP segments and loyalty points, coupons,
30-day analytics with profit and VAT estimate, store settings and plan/billing.

**Storefront** (`/s/<store>/`): branded per store colour, category/search/sort, product pages
with variants and bilingual descriptions, session bag with coupons, checkout with delivery-area
fees, **OTP phone verification**, delivery-fee advance for high-risk COD orders, order
confirmation and order tracking.

**Business rules from the pitch**: Shuru ৳0 / Growth ৳799 / Business ৳1,799 / Scale ৳3,999,
annual = 2 months free, unlimited orders on paid plans, plan product and AI-listing limits,
30-day trial extended to 60/90 days at 10/50 orders, cross-store fraud history.

## Run it

```bash
pip install -r requirements.txt
python manage.py migrate          # also seeds plans and FAQs
python manage.py seed_demo        # demo seller + "Nakshi Threads" store with 30 days of orders
python manage.py createsuperuser  # optional, for /admin/
python manage.py runserver
```

- Site: http://127.0.0.1:8000/
- Demo store: http://127.0.0.1:8000/s/nakshi-threads/
- Dashboard: http://127.0.0.1:8000/dashboard/ — `demo@dokan.ai` / `demo12345`

Run the tests with `python manage.py test`.

## Configuration

| Variable | Purpose |
|---|---|
| `DJANGO_SECRET_KEY`, `DJANGO_DEBUG`, `DJANGO_ALLOWED_HOSTS`, `DJANGO_CSRF_TRUSTED_ORIGINS` | Standard Django deployment settings |
| `ANTHROPIC_API_KEY` | Turns on Claude vision for AI Snap & Sell (`AI_ENABLED` defaults to on when set) |
| `AI_MODEL` | Claude model id, default `claude-opus-5` |
| `OTP_SHOW_ON_SCREEN` | Show checkout OTP codes on screen (defaults to `DEBUG`); wire a gateway in `stores/services/otp.py:send_sms` |
| `BRAND_NAME`, `BRAND_EMAIL`, `BRAND_PHONE` | Brand details used across the site |

Without an API key, Snap & Sell uses a built-in template writer so the feature always works.
Marketing copy and pitch figures live in `core/content.py`; team names are placeholders to fill in.
