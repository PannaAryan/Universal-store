"""Static marketing content, taken from the investor pitch deck.

Kept in one module so every page renders from the same facts and sources.
"""

HERO_STATS = [
    {"value": "2–2.5 lakh", "label": "F-commerce sellers in Bangladesh"},
    {"value": "10 min", "label": "from signup to a live store"},
    {"value": "99.9%", "label": "uptime SLA with service credits"},
    {"value": "0", "label": "order caps on any paid plan"},
]

PROBLEM_STATS = [
    {"value": "2–2.5 lakh", "label": "F-commerce entrepreneurs run their shop from Facebook pages"},
    {"value": "~2,000", "label": "dedicated e-commerce sites, versus 3 lakh+ Facebook selling pages"},
    {"value": "৳100–200", "label": "lost in two-way courier fees on every failed COD delivery"},
]
PROBLEM_SOURCES = "e-CAB via The Business Standard (2024); Dhaka Tribune (2023); Banikh courier guide (2026)"

DIGITAL_STATS = [
    {"value": "82.8M", "label": "internet users (late 2025)"},
    {"value": "64.0M", "label": "social media user identities"},
    {"value": "239.3M", "label": "mobile money accounts (Jan 2025)"},
    {"value": "90%+", "label": "of online buyers prefer cash on delivery"},
]
DIGITAL_SOURCES = "DataReportal Digital 2026; Bangladesh Bank via Financial Express; DHL (2025); The Business Standard (2024)"

SNAP_STEPS = [
    {"n": "1", "title": "Upload a photo", "text": "Plus a short title and price, straight from your phone."},
    {"n": "2", "title": "AI writes the listing", "text": "Bangla and English description, variants, tags and SEO."},
    {"n": "3", "title": "Sell everywhere", "text": "Published to your store, Facebook and Instagram."},
]

MODULES = [
    {"icon": "store", "title": "Store & domain", "text": "Own domain, hosting, SSL, themes and branding."},
    {"icon": "sparkle", "title": "Catalog & AI", "text": "Variants, bulk upload, AI-written listings."},
    {"icon": "box", "title": "Inventory", "text": "Real-time stock, low-stock alerts, multi-warehouse."},
    {"icon": "truck", "title": "Orders & couriers", "text": "Full order lifecycle with Pathao, Steadfast and RedX."},
    {"icon": "wallet", "title": "Payments & finance", "text": "bKash, Nagad, SSLCommerz and COD; P&L and VAT."},
    {"icon": "users", "title": "Customers", "text": "OTP login, history, segments, loyalty and coupons."},
    {"icon": "megaphone", "title": "Marketing", "text": "SMS and email, Meta Pixel, abandoned-cart recovery."},
    {"icon": "chart", "title": "Team & analytics", "text": "Roles, activity logs, sales and conversion reports."},
]

PAIN_POINTS = [
    ("Fake COD orders and returns", "OTP checkout, courier-history risk score, partial advance"),
    ("Manual order taking in Messenger", "AI order bot on your store, Messenger and WhatsApp"),
    ("Writing product titles and descriptions", "AI Snap & Sell writes them from one photo"),
    ("Slow or missing support", "7-day Bangla support, first reply in under 15 minutes"),
    ("Server downtime during campaigns", "99.9% uptime SLA, auto-scaling, public status page"),
    ("Order caps and confusing pricing", "Unlimited orders on every paid plan"),
    ("Hard-to-use dashboards", "10-minute wizard setup, Bangla interface, mobile app"),
]

# "unique" = no local competitor offers it together; "better" = done better than competitors.
USPS = [
    {"icon": "camera", "title": "AI Snap & Sell", "text": "Photo in, full product listing out.", "tone": "unique"},
    {"icon": "chat", "title": "AI sales assistant", "text": "Answers and takes orders 24/7 in Bangla.", "tone": "unique"},
    {"icon": "infinity", "title": "Unlimited orders", "text": "No order caps on any paid plan.", "tone": "unique"},
    {"icon": "pulse", "title": "99.9% uptime SLA", "text": "Service credits and a public status page.", "tone": "unique"},
    {"icon": "headset", "title": "Real support", "text": "7-day Bangla help, onboarding call, free migration.", "tone": "better"},
    {"icon": "shield", "title": "Fewer returns", "text": "OTP, risk score and partial advance payment.", "tone": "better"},
    {"icon": "clock", "title": "10-minute setup", "text": "Wizard onboarding, Bangla UI, mobile app.", "tone": "better"},
    {"icon": "key", "title": "Own your customers", "text": "Your website and data, safe from Facebook shocks.", "tone": "better"},
]

COMPETITORS = [
    {"name": "Shopify (global)", "price": "US$39 (≈৳4,760)", "scale": "Global leader", "gap": "USD billing, no Bangla admin, bKash via apps"},
    {"name": "Zatiq Easy", "price": "Free; ৳599–2,499", "scale": "~50k active shops; raised US$1.6M", "gap": "No AI listing or AI chat ordering listed"},
    {"name": "Storola", "price": "৳990–4,990", "scale": "1,000–3,000+", "gap": "Higher price, busy interface"},
    {"name": "StoreX", "price": "৳990–4,990", "scale": "5,000+", "gap": "Little company transparency"},
    {"name": "Soppiya", "price": "US$8–45", "scale": "Not disclosed", "gap": "USD pricing, product limits"},
    {"name": "Boneek", "price": "~৳2,490–3,300", "scale": "Conflicting claims", "gap": "Monthly order caps, very new"},
    {"name": "Zobity / eBitans / others", "price": "Free or unpublished", "scale": "Unproven", "gap": "Reliability and support unknown"},
]
COMPETITOR_SOURCES = "Our competitor research; Pitchbook (Zatiq Easy funding); Shopify US monthly pricing via ShopExperts (Aug 2026)"

COMPARE_MATRIX = {
    "columns": ["Us", "Zatiq Easy", "Storola", "StoreX", "Shopify"],
    "rows": [
        ("AI listing from a photo", ["yes", "no", "no", "no", "app"]),
        ("AI chat ordering in Bangla", ["yes", "no", "no", "no", "no"]),
        ("Unlimited orders on paid plans", ["yes", "yes", "yes", "yes", "yes"]),
        ("Uptime SLA with credits", ["yes", "no", "no", "no", "yes"]),
        ("bKash & Nagad built in", ["yes", "yes", "yes", "yes", "app"]),
        ("Pathao, Steadfast, RedX", ["yes", "yes", "yes", "yes", "app"]),
        ("COD fraud risk score", ["yes", "no", "no", "no", "no"]),
        ("Bangla admin interface", ["yes", "yes", "yes", "yes", "no"]),
        ("BDT billing", ["yes", "yes", "yes", "yes", "no"]),
        ("7-day Bangla support", ["yes", "partial", "partial", "partial", "no"]),
    ],
}

PLAN_ADDONS = ["SMS packs", "AI credits", "Branded buyer apps", "Premium themes"]

MARKET_STATS = [
    {"value": "US$7.41B", "label": "Bangladesh B2C e-commerce in 2025"},
    {"value": "US$15.4B", "label": "forecast for 2029, at a 17.7% CAGR"},
    {"value": "65%", "label": "of digital commerce sales come from F-commerce sellers"},
]
MARKET_SOURCES = "ResearchAndMarkets Databook (Jan 2026); ECDB via DHL (2025); Pathao CEO in The Business Standard (Aug 2024)"

TAM = [
    {"tier": "TAM", "who": "~5 lakh Facebook business pages and sellers moving online", "value": "~৳600 crore", "sub": "≈US$49M a year"},
    {"tier": "SAM", "who": "2–2.5 lakh active F-commerce sellers", "value": "৳240–300 crore", "sub": "a year"},
    {"tier": "SOM", "who": "35,000 paying stores by Year 5", "value": "৳59 crore", "sub": "ARR"},
]

UNIT_ECONOMICS = [
    {"value": "৳1,100", "label": "blended revenue per store per month"},
    {"value": "~75%", "label": "gross margin after hosting, AI and SMS"},
    {"value": "৳3,000", "label": "maximum cost to acquire a paying store"},
    {"value": "5.5x", "label": "lifetime value to acquisition cost"},
]

PROJECTIONS = [
    {"year": "Year 1", "stores": "1,500", "arr": 2.0},
    {"year": "Year 2", "stores": "5,000", "arr": 7.2},
    {"year": "Year 3", "stores": "12,000", "arr": 18.0},
    {"year": "Year 4", "stores": "22,000", "arr": 34.3},
    {"year": "Year 5", "stores": "35,000", "arr": 58.8},
]

GTM = [
    {"icon": "users", "title": "Facebook seller groups", "text": "Free Bangla workshops and live AI demos."},
    {"icon": "truck", "title": "Courier partners", "text": "Co-marketing to Pathao, Steadfast and RedX merchants."},
    {"icon": "wallet", "title": "Payment partners", "text": "bKash and Nagad merchant onboarding bundles."},
    {"icon": "heart", "title": "Women-led networks", "text": "Partnerships with e-CAB, SME Foundation and women's groups."},
    {"icon": "gift", "title": "Referral and migration", "text": "Free month per referral; free switch from other builders."},
    {"icon": "play", "title": "Bangla video content", "text": "YouTube and TikTok tutorials and seller success stories."},
]

ROADMAP = [
    {"phase": "MVP", "when": "Months 0–4", "text": "Store builder, catalog, orders, COD and bKash, 3 couriers, AI Snap & Sell, OTP login.", "gate": "100 pilot sellers live"},
    {"phase": "Launch", "when": "Months 5–8", "text": "Finance, inventory alerts, Pixel and CAPI, fraud shield, seller mobile app.", "gate": "1,000 active stores, 30% trial-to-paid"},
    {"phase": "Growth", "when": "Months 9–14", "text": "AI chat bot on store, Messenger and WhatsApp; FB and IG catalog sync; marketing automation.", "gate": "5,000 paying stores"},
    {"phase": "Scale", "when": "Months 15–24", "text": "Multi-warehouse, POS, branded buyer app, open API, theme and app marketplace.", "gate": "Monthly break-even"},
]

RISKS = [
    ("Price war from free plans", "Compete on AI, reliability and support; keep a generous free tier"),
    ("High churn among micro-sellers", "Milestone trial, onboarding calls, discounted annual plans"),
    ("Facebook policy or API changes", "Own-website first; Instagram, TikTok and WhatsApp channels"),
    ("Outages or internet disruption", "Multi-region hosting, auto-scaling, offline order capture"),
    ("Rising AI costs", "Usage-based AI credits, model routing and caching"),
    ("Competitors copy AI features", "Ship fast; build network effects like shared fraud data"),
]

USE_OF_FUNDS = [
    {"label": "Product and engineering", "pct": 40},
    {"label": "Marketing and seller acquisition", "pct": 30},
    {"label": "Support and onboarding team", "pct": 15},
    {"label": "Cloud infrastructure and AI", "pct": 10},
    {"label": "Legal, compliance and admin", "pct": 5},
]

TEAM = [
    {"name": "Founder name", "role": "CEO / Co-founder", "bio": "Relevant experience goes here."},
    {"name": "Founder name", "role": "CTO / Co-founder", "bio": "Relevant experience goes here."},
    {"name": "Team member", "role": "Head of Growth", "bio": "Relevant experience goes here."},
    {"name": "Advisor", "role": "Advisor", "bio": "Relevant experience goes here."},
]

INTEGRATIONS = ["bKash", "Nagad", "SSLCommerz", "Pathao", "Steadfast", "RedX", "Meta Pixel", "WhatsApp", "Messenger", "Instagram"]

STATUS_COMPONENTS = [
    "Storefronts", "Seller dashboard", "Checkout & OTP", "Payments (bKash, Nagad, SSLCommerz)",
    "Courier sync", "AI Snap & Sell", "SMS & email", "Mobile app API",
]

SELLER_CATEGORIES = ["Fashion", "Cosmetics & beauty", "Home décor", "Electronics", "Food & grocery", "Handicrafts", "Kids & baby", "Other"]
