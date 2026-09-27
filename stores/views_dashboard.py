from datetime import timedelta
from decimal import Decimal
from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count, F, Q, Sum
from django.db.models.functions import TruncDate
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from core.models import Plan

from .forms import (
    AIGenerateForm, CouponForm, ManualOrderForm, OnboardingForm, OrderUpdateForm, ProductForm, StoreSettingsForm,
)
from .models import Coupon, Customer, Order, OrderItem, Product
from .services import orders as order_service
from .services.ai import generate_listing

PAID_STATUSES = [Order.Status.CONFIRMED, Order.Status.PACKED, Order.Status.SHIPPED, Order.Status.DELIVERED]


def store_required(view):
    """Require a signed-in seller with a store; send new sellers to onboarding."""

    @login_required
    @wraps(view)
    def wrapper(request, *args, **kwargs):
        store = request.user.stores.select_related("plan").first()
        if store is None:
            return redirect("dashboard:onboarding")
        request.store = store
        return view(request, *args, **kwargs)

    return wrapper


def _daily_series(store, days):
    start = timezone.localdate() - timedelta(days=days - 1)
    rows = (
        store.orders.filter(created_at__date__gte=start)
        .exclude(status__in=[Order.Status.CANCELLED, Order.Status.RETURNED])
        .annotate(day=TruncDate("created_at"))
        .values("day").annotate(revenue=Sum("total"), orders=Count("id"))
    )
    by_day = {r["day"]: r for r in rows}
    series = []
    for i in range(days):
        day = start + timedelta(days=i)
        r = by_day.get(day, {})
        series.append({"day": day, "revenue": r.get("revenue") or Decimal(0), "orders": r.get("orders") or 0})
    peak = max((s["revenue"] for s in series), default=0) or 1
    for s in series:
        s["pct"] = round(float(s["revenue"]) / float(peak) * 100, 1)
    return series


@login_required
def onboarding(request):
    if request.user.stores.exists():
        return redirect("dashboard:home")
    plans = Plan.objects.all()
    chosen = request.session.get("chosen_plan", "growth")
    form = OnboardingForm(request.POST or None, initial={
        "phone": getattr(request.user.profile, "phone", ""), "brand_color": "#1E7F5C", "theme": "bazaar",
    })
    if request.method == "POST" and form.is_valid():
        store = form.save(commit=False)
        store.owner = request.user
        store.email = request.user.email
        store.plan = plans.filter(slug=request.POST.get("plan") or chosen).first() or plans.first()
        store.save()
        request.session.pop("chosen_plan", None)
        messages.success(request, f"{store.name} is live! Add your first product with AI Snap & Sell.")
        return redirect("dashboard:product_add")
    return render(request, "dashboard/onboarding.html", {"form": form, "plans": plans, "chosen": chosen})


@store_required
def home(request):
    store = request.store
    now = timezone.now()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    month_orders = store.orders.filter(created_at__gte=month_start)
    valid = month_orders.exclude(status__in=[Order.Status.CANCELLED, Order.Status.RETURNED])
    revenue = valid.aggregate(s=Sum("total"))["s"] or 0
    order_count = valid.count()
    kpis = [
        {"label": "Revenue this month", "value": f"৳{revenue:,.0f}", "icon": "wallet"},
        {"label": "Orders this month", "value": order_count, "icon": "bag"},
        {"label": "Average order value", "value": f"৳{(revenue / order_count if order_count else 0):,.0f}", "icon": "chart"},
        {"label": "Pending orders", "value": store.orders.filter(status=Order.Status.PENDING).count(), "icon": "clock"},
    ]
    has_product = store.products.exists()
    checklist = [
        {"label": "Create your store", "done": True, "url": "dashboard:settings"},
        {"label": "Add a product with AI Snap & Sell", "done": has_product, "url": "dashboard:product_add"},
        {"label": "Set delivery fees and couriers", "done": store.courier_list != [] and store.delivery_fee_dhaka > 0, "url": "dashboard:settings"},
        {"label": "Get your first order", "done": store.orders.exists(), "url": "dashboard:order_add"},
        {"label": "Share your store link", "done": store.orders.filter(source="store").exists(), "url": None},
    ]
    return render(request, "dashboard/home.html", {
        "kpis": kpis,
        "recent_orders": store.orders.select_related("customer")[:6],
        "low_stock": store.products.filter(stock__lte=F("low_stock_threshold"), is_active=True)[:5],
        "series": _daily_series(store, 14),
        "checklist": checklist,
        "checklist_done": sum(c["done"] for c in checklist),
        "risky": store.orders.filter(status=Order.Status.PENDING, risk_score__gte=60).count(),
    })


# --- Products -----------------------------------------------------------------

@store_required
def products(request):
    qs = request.store.products.select_related("category")
    q = request.GET.get("q", "").strip()
    view = request.GET.get("filter", "all")
    if q:
        qs = qs.filter(Q(title__icontains=q) | Q(sku__icontains=q) | Q(tags__icontains=q))
    if view == "low":
        qs = qs.filter(stock__lte=F("low_stock_threshold"))
    elif view == "hidden":
        qs = qs.filter(is_active=False)
    elif view == "ai":
        qs = qs.filter(ai_generated=True)
    page = Paginator(qs, 12).get_page(request.GET.get("page"))
    return render(request, "dashboard/products.html", {"page": page, "q": q, "filter": view})


@store_required
def product_edit(request, pk=None):
    store = request.store
    product = get_object_or_404(Product, pk=pk, store=store) if pk else None
    plan = store.plan
    if product is None and plan and plan.product_limit is not None and store.products.count() >= plan.product_limit:
        messages.warning(request, f"Your {plan.name} plan allows {plan.product_limit} products. Upgrade to add more.")
        return redirect("dashboard:billing")
    form = ProductForm(request.POST or None, request.FILES or None, instance=product, store=store)
    if request.method == "POST" and form.is_valid():
        saved = form.save()
        messages.success(request, f"“{saved.title}” {'updated' if product else 'added to your store'}.")
        if "save_add" in request.POST:
            return redirect("dashboard:product_add")
        return redirect("dashboard:products")
    quota = store.ai_quota()
    return render(request, "dashboard/product_form.html", {
        "form": form, "product": product,
        "ai_used": store.ai_listings_this_month(), "ai_quota": quota,
    })


@store_required
@require_POST
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk, store=request.store)
    if OrderItem.objects.filter(product=product).exists():
        product.is_active = False
        product.save(update_fields=["is_active"])
        messages.info(request, f"“{product.title}” has orders, so it was hidden instead of deleted.")
    else:
        product.delete()
        messages.success(request, f"“{product.title}” deleted.")
    return redirect("dashboard:products")


@store_required
@require_POST
def ai_generate(request):
    store = request.store
    quota = store.ai_quota()
    if quota is not None and store.ai_listings_this_month() >= quota:
        return JsonResponse({"ok": False, "error": f"You've used all {quota} AI listings this month. Upgrade for more."}, status=402)
    form = AIGenerateForm(request.POST, request.FILES)
    if not form.is_valid():
        return JsonResponse({"ok": False, "errors": form.errors}, status=400)
    listing = generate_listing(
        title=form.cleaned_data["title"], price=form.cleaned_data["price"],
        category=store.category, image=form.cleaned_data.get("image"),
    )
    return JsonResponse({"ok": True, "listing": listing})


# --- Orders -------------------------------------------------------------------

@store_required
def orders(request):
    qs = request.store.orders.select_related("customer")
    status = request.GET.get("status", "")
    q = request.GET.get("q", "").strip()
    if status == "risky":
        qs = qs.filter(risk_score__gte=60).exclude(status__in=[Order.Status.DELIVERED, Order.Status.CANCELLED])
    elif status:
        qs = qs.filter(status=status)
    if q:
        qs = qs.filter(Q(number__icontains=q) | Q(shipping_name__icontains=q) | Q(shipping_phone__icontains=q))
    counts = dict(request.store.orders.values_list("status").annotate(n=Count("id")))
    tabs = [("", "All", sum(counts.values()))] + [
        (k, label, counts.get(k, 0)) for k, label in Order.Status.choices
    ]
    page = Paginator(qs, 15).get_page(request.GET.get("page"))
    return render(request, "dashboard/orders.html", {"page": page, "tabs": tabs, "status": status, "q": q})


@store_required
def order_detail(request, number):
    order = get_object_or_404(Order.objects.select_related("customer", "coupon"), number=number, store=request.store)
    form = OrderUpdateForm(request.POST or None, instance=order)
    if request.method == "POST" and form.is_valid():
        previous = Order.objects.get(pk=order.pk).status
        updated = form.save()
        restock = {Order.Status.CANCELLED, Order.Status.RETURNED}
        if updated.status in restock and previous not in restock:
            for item in updated.items.exclude(product=None):
                Product.objects.filter(pk=item.product_id).update(stock=F("stock") + item.quantity)
        messages.success(request, f"Order #{order.number} updated.")
        return redirect("dashboard:order_detail", number=order.number)
    from .services.risk import risk_score

    _, reasons = risk_score(order.shipping_phone, order.total, order.payment_method)
    history = order.customer.orders.exclude(pk=order.pk)[:5]
    return render(request, "dashboard/order_detail.html", {
        "order": order, "form": form, "risk_reasons": reasons, "history": history,
    })


@store_required
def order_add(request):
    store = request.store
    form = ManualOrderForm(request.POST or None, store=store)
    if request.method == "POST" and form.is_valid():
        d = form.cleaned_data
        try:
            order = order_service.place_order(
                store, name=d["name"], phone=d["phone"], address=d["address"], city=d["city"],
                inside_dhaka=d["inside_dhaka"], payment_method=d["payment_method"], note=d["note"],
                items=[(p, q, "") for p, q in form.items()], source=d["source"],
            )
        except order_service.OutOfStock as exc:
            form.add_error(None, str(exc))
        else:
            messages.success(request, f"Order #{order.number} created.")
            return redirect("dashboard:order_detail", number=order.number)
    return render(request, "dashboard/order_add.html", {"form": form})


# --- Customers & coupons --------------------------------------------------------

@store_required
def customers(request):
    qs = request.store.customers.annotate(
        order_count=Count("orders"),
        spent=Sum("orders__total", filter=Q(orders__status__in=PAID_STATUSES)),
    )
    q = request.GET.get("q", "").strip()
    if q:
        qs = qs.filter(Q(name__icontains=q) | Q(phone__icontains=q))
    segment = request.GET.get("segment", "")
    if segment == "vip":
        qs = qs.filter(order_count__gte=5)
    elif segment == "repeat":
        qs = qs.filter(order_count__gte=2, order_count__lt=5)
    elif segment == "new":
        qs = qs.filter(order_count__lt=2)
    page = Paginator(qs.order_by("-spent", "-created_at"), 20).get_page(request.GET.get("page"))
    return render(request, "dashboard/customers.html", {"page": page, "q": q, "segment": segment})


@store_required
def coupons(request):
    store = request.store
    form = CouponForm(request.POST or None, store=store)
    if request.method == "POST" and form.is_valid():
        coupon = form.save(commit=False)
        coupon.store = store
        coupon.save()
        messages.success(request, f"Coupon {coupon.code} created.")
        return redirect("dashboard:coupons")
    return render(request, "dashboard/coupons.html", {"form": form, "coupons": store.coupons.all()})


@store_required
@require_POST
def coupon_toggle(request, pk):
    coupon = get_object_or_404(Coupon, pk=pk, store=request.store)
    coupon.is_active = not coupon.is_active
    coupon.save(update_fields=["is_active"])
    return redirect("dashboard:coupons")


# --- Analytics, settings, billing ---------------------------------------------

@store_required
def analytics(request):
    store = request.store
    days = 30
    since = timezone.now() - timedelta(days=days)
    recent = store.orders.filter(created_at__gte=since)
    valid = recent.exclude(status__in=[Order.Status.CANCELLED, Order.Status.RETURNED])
    total_orders = recent.count()
    delivered = recent.filter(status=Order.Status.DELIVERED).count()
    returned = recent.filter(status=Order.Status.RETURNED).count()
    revenue = valid.aggregate(s=Sum("total"))["s"] or 0
    cost = (
        OrderItem.objects.filter(order__in=valid, product__cost_price__isnull=False)
        .aggregate(s=Sum(F("product__cost_price") * F("quantity")))["s"] or 0
    )

    def split(field, choices):
        rows = dict(recent.values_list(field).annotate(n=Count("id")))
        return [
            {"label": label, "n": rows.get(key, 0), "pct": round(rows.get(key, 0) / total_orders * 100) if total_orders else 0}
            for key, label in choices if rows.get(key)
        ]

    top = (
        OrderItem.objects.filter(order__in=valid).values("title")
        .annotate(qty=Sum("quantity"), revenue=Sum(F("unit_price") * F("quantity"))).order_by("-revenue")[:5]
    )
    return render(request, "dashboard/analytics.html", {
        "series": _daily_series(store, days),
        "stats": [
            {"label": "Revenue (30 days)", "value": f"৳{revenue:,.0f}"},
            {"label": "Gross profit (est.)", "value": f"৳{(revenue - cost):,.0f}" if cost else "Add cost prices"},
            {"label": "Delivery success", "value": f"{round(delivered / (delivered + returned) * 100) if delivered + returned else 0}%"},
            {"label": "Orders (30 days)", "value": total_orders},
        ],
        "by_status": split("status", Order.Status.choices),
        "by_source": split("source", Order._meta.get_field("source").choices),
        "by_payment": split("payment_method", Order._meta.get_field("payment_method").choices),
        "top_products": top,
        "vat_estimate": round(float(revenue) * 0.05),
    })


@store_required
def store_settings(request):
    form = StoreSettingsForm(request.POST or None, request.FILES or None, instance=request.store)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Store settings saved.")
        return redirect("dashboard:settings")
    return render(request, "dashboard/settings.html", {"form": form})


@store_required
def billing(request):
    store = request.store
    if request.method == "POST":
        plan = get_object_or_404(Plan, slug=request.POST.get("plan"))
        cycle = request.POST.get("cycle", "monthly")
        if plan.product_limit is not None and store.products.count() > plan.product_limit:
            messages.error(request, f"{plan.name} allows {plan.product_limit} products — hide or remove some first.")
        else:
            store.plan = plan
            store.billing_cycle = cycle if cycle in {"monthly", "annual"} else "monthly"
            store.save(update_fields=["plan", "billing_cycle"])
            messages.success(request, f"You're now on the {plan.name} plan.")
        return redirect("dashboard:billing")
    return render(request, "dashboard/billing.html", {
        "plans": Plan.objects.all(),
        "ai_used": store.ai_listings_this_month(),
        "product_count": store.products.count(),
        "customer_count": Customer.objects.filter(store=store).count(),
    })
